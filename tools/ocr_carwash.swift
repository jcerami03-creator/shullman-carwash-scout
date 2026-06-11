import AppKit
import Foundation
import PDFKit
import Vision

struct PageOCR: Codable {
    let page: Int
    let text: String
}

struct DocumentOCR: Codable {
    let file: String
    let pages: [PageOCR]
}

func usage() -> Never {
    fputs("Usage: swift tools/ocr_carwash.swift <pdf-folder-or-file> <output-folder> [max-pages-per-pdf]\n", stderr)
    exit(2)
}

guard CommandLine.arguments.count >= 3 else {
    usage()
}

let inputURL = URL(fileURLWithPath: CommandLine.arguments[1])
let outputFolder = URL(fileURLWithPath: CommandLine.arguments[2])
let maxPages = CommandLine.arguments.count >= 4 ? Int(CommandLine.arguments[3]) : nil

try FileManager.default.createDirectory(at: outputFolder, withIntermediateDirectories: true)

let isDirectory = (try? inputURL.resourceValues(forKeys: [.isDirectoryKey]).isDirectory) ?? false
let pdfFiles: [URL]
if isDirectory {
    pdfFiles = (try FileManager.default.contentsOfDirectory(
        at: inputURL,
        includingPropertiesForKeys: nil
    ))
        .filter { $0.pathExtension.lowercased() == "pdf" }
        .sorted { $0.lastPathComponent < $1.lastPathComponent }
} else {
    pdfFiles = inputURL.pathExtension.lowercased() == "pdf" ? [inputURL] : []
}

func renderPage(_ page: PDFPage, scale: CGFloat = 1.35) -> CGImage? {
    let bounds = page.bounds(for: .mediaBox)
    let size = CGSize(width: bounds.width * scale, height: bounds.height * scale)
    let image = page.thumbnail(of: size, for: .mediaBox)
    var proposedRect = CGRect(origin: .zero, size: image.size)
    return image.cgImage(forProposedRect: &proposedRect, context: nil, hints: nil)
}

func recognizeText(in image: CGImage) throws -> String {
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = true
    request.recognitionLanguages = ["en-US"]

    let handler = VNImageRequestHandler(cgImage: image, options: [:])
    try handler.perform([request])

    let observations = request.results ?? []
    return observations
        .compactMap { $0.topCandidates(1).first?.string }
        .joined(separator: "\n")
}

let encoder = JSONEncoder()
encoder.outputFormatting = [.prettyPrinted, .sortedKeys]

for pdfURL in pdfFiles {
    print("Opening \(pdfURL.lastPathComponent)")
    fflush(stdout)

    guard let document = PDFDocument(url: pdfURL) else {
        print("Could not open \(pdfURL.lastPathComponent)")
        continue
    }

    let pageCount = maxPages.map { min($0, document.pageCount) } ?? document.pageCount
    var pages: [PageOCR] = []
    print("OCR \(pdfURL.lastPathComponent) pages \(pageCount)/\(document.pageCount)")
    fflush(stdout)

    for pageIndex in 0..<pageCount {
        autoreleasepool {
            guard let page = document.page(at: pageIndex), let image = renderPage(page) else {
                pages.append(PageOCR(page: pageIndex + 1, text: ""))
                return
            }

            do {
                let text = try recognizeText(in: image)
                pages.append(PageOCR(page: pageIndex + 1, text: text))
                print("  page \(pageIndex + 1): \(text.count) chars")
                fflush(stdout)
            } catch {
                pages.append(PageOCR(page: pageIndex + 1, text: ""))
                print("  page \(pageIndex + 1): OCR failed \(error)")
                fflush(stdout)
            }
        }
    }

    let result = DocumentOCR(file: pdfURL.lastPathComponent, pages: pages)
    let jsonURL = outputFolder.appendingPathComponent(pdfURL.deletingPathExtension().lastPathComponent + ".json")
    let textURL = outputFolder.appendingPathComponent(pdfURL.deletingPathExtension().lastPathComponent + ".txt")

    let jsonData = try encoder.encode(result)
    try jsonData.write(to: jsonURL)

    let text = pages.map { "--- PAGE \($0.page) ---\n\($0.text)" }.joined(separator: "\n\n")
    try text.write(to: textURL, atomically: true, encoding: .utf8)
}
