import AppKit
import Foundation
import PDFKit

func usage() -> Never {
    fputs("Usage: swift tools/render_pdf_gallery.swift <input-pdf> <output-folder> [max-width]\n", stderr)
    exit(2)
}

guard CommandLine.arguments.count >= 3 else {
    usage()
}

let inputURL = URL(fileURLWithPath: CommandLine.arguments[1])
let outputURL = URL(fileURLWithPath: CommandLine.arguments[2])
let maxWidth = CommandLine.arguments.count >= 4 ? CGFloat(Double(CommandLine.arguments[3]) ?? 980) : 980

try FileManager.default.createDirectory(at: outputURL, withIntermediateDirectories: true)

guard let document = PDFDocument(url: inputURL) else {
    fputs("Could not open PDF: \(inputURL.path)\n", stderr)
    exit(1)
}

for pageIndex in 0..<document.pageCount {
    autoreleasepool {
        guard let page = document.page(at: pageIndex) else { return }
        let bounds = page.bounds(for: .mediaBox)
        let scale = min(maxWidth / max(bounds.width, 1), 2.0)
        let size = NSSize(width: bounds.width * scale, height: bounds.height * scale)
        let image = NSImage(size: size)

        image.lockFocus()
        NSColor.white.setFill()
        NSRect(origin: .zero, size: size).fill()

        guard let context = NSGraphicsContext.current?.cgContext else {
            image.unlockFocus()
            return
        }

        context.saveGState()
        context.scaleBy(x: scale, y: scale)
        page.draw(with: .mediaBox, to: context)
        context.restoreGState()
        image.unlockFocus()

        guard
            let tiff = image.tiffRepresentation,
            let bitmap = NSBitmapImageRep(data: tiff),
            let jpg = bitmap.representation(using: .jpeg, properties: [.compressionFactor: 0.78])
        else {
            print("Could not render page \(pageIndex + 1)")
            return
        }

        let filename = String(format: "page-%03d.jpg", pageIndex + 1)
        let target = outputURL.appendingPathComponent(filename)
        do {
            try jpg.write(to: target)
            print("Rendered \(filename)")
        } catch {
            print("Could not write \(filename): \(error)")
        }
    }
}
