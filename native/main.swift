import Cocoa
import WebKit

let appName = "Lalitha Sahasranama"
let baseURL = URL(string: "https://hrishim.github.io/lalitha_sahasranamam_pwa/book/")!

final class AppDelegate: NSObject, NSApplicationDelegate, WKNavigationDelegate {
    var window: NSWindow!
    var webView: WKWebView!
    let fm = FileManager.default

    var supportDir: URL {
        let base = fm.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        return base.appendingPathComponent("LalithaSahasranamaBook", isDirectory: true)
    }
    var liveDir: URL { return supportDir.appendingPathComponent("book", isDirectory: true) }
    var bundledDir: URL { return Bundle.main.resourceURL!.appendingPathComponent("book", isDirectory: true) }

    func currentDir() -> URL {
        let index = liveDir.appendingPathComponent("index.html")
        return fm.fileExists(atPath: index.path) ? liveDir : bundledDir
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        buildMenu()
        webView = WKWebView(frame: .zero, configuration: WKWebViewConfiguration())
        webView.setValue(false, forKey: "drawsBackground")
        webView.navigationDelegate = self
        webView.allowsMagnification = true

        let rect = NSRect(x: 0, y: 0, width: 1280, height: 860)
        window = NSWindow(contentRect: rect,
                          styleMask: [.titled, .closable, .miniaturizable, .resizable],
                          backing: .buffered,
                          defer: false)
        window.title = appName
        window.contentView = webView
        window.backgroundColor = NSColor(calibratedRed: 0.827, green: 0.706, blue: 0.478, alpha: 1)
        window.minSize = NSSize(width: 480, height: 480)
        let key = "NSWindow Frame MainWindow"
        if UserDefaults.standard.string(forKey: key) == nil { window.center() }
        window.setFrameAutosaveName("MainWindow")
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)

        loadBook()
        updateInBackground()
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return true
    }

    func loadBook() {
        let dir = currentDir()
        webView.loadFileURL(dir.appendingPathComponent("index.html"), allowingReadAccessTo: dir)
    }

    @objc func reloadBook() { loadBook() }

    // Open web links in the default browser; keep book pages inside the window.
    func webView(_ webView: WKWebView,
                 decidePolicyFor navigationAction: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        if let url = navigationAction.request.url, let scheme = url.scheme,
           scheme == "http" || scheme == "https" {
            NSWorkspace.shared.open(url)
            decisionHandler(.cancel)
            return
        }
        decisionHandler(.allow)
    }

    func fetch(_ url: URL) -> Data? {
        var request = URLRequest(url: url)
        request.timeoutInterval = 15
        request.cachePolicy = .reloadIgnoringLocalCacheData
        let semaphore = DispatchSemaphore(value: 0)
        var result: Data? = nil
        URLSession.shared.dataTask(with: request) { data, response, _ in
            if let http = response as? HTTPURLResponse, http.statusCode == 200 { result = data }
            semaphore.signal()
        }.resume()
        semaphore.wait()
        return result
    }

    func updateInBackground() {
        DispatchQueue.global(qos: .utility).async {
            guard let manifestData = self.fetch(baseURL.appendingPathComponent("manifest.txt")),
                  let manifest = String(data: manifestData, encoding: .utf8) else { return }
            let lines: [String] = manifest
                .components(separatedBy: .newlines)
                .map { $0.trimmingCharacters(in: .whitespaces) }
                .filter { !$0.isEmpty }
            guard let version = lines.first else { return }

            var oldVersion: String? = nil
            if let old = try? String(contentsOf: self.liveDir.appendingPathComponent("manifest.txt"), encoding: .utf8) {
                oldVersion = old.components(separatedBy: .newlines).first
            }
            if oldVersion == version { return }

            let tmp = self.supportDir.appendingPathComponent("tmp-" + UUID().uuidString, isDirectory: true)
            do {
                try self.fm.createDirectory(at: tmp, withIntermediateDirectories: true)
                try manifestData.write(to: tmp.appendingPathComponent("manifest.txt"))
                for name in lines.dropFirst() {
                    guard let data = self.fetch(baseURL.appendingPathComponent(name)) else {
                        throw URLError(.cannotLoadFromNetwork)
                    }
                    try data.write(to: tmp.appendingPathComponent(name))
                }
                if !self.fm.fileExists(atPath: tmp.appendingPathComponent("index.html").path) {
                    throw URLError(.fileDoesNotExist)
                }
                if self.fm.fileExists(atPath: self.liveDir.path) {
                    try self.fm.removeItem(at: self.liveDir)
                }
                try self.fm.moveItem(at: tmp, to: self.liveDir)
            } catch {
                try? self.fm.removeItem(at: tmp)
                return
            }
        }
    }

    // After an update, switch to the new copy only if the reader is still on the cover.
    func reloadIfAtStart() {
        let js = "(document.getElementById('pg')||{}).textContent||''"
        webView.evaluateJavaScript(js) { result, _ in
            if let label = result as? String, label.hasPrefix("Cover") || label.hasPrefix("Page 1 ") {
                self.loadBook()
            }
        }
    }

    func buildMenu() {
        let mainMenu = NSMenu()
        NSApp.mainMenu = mainMenu

        let appItem = NSMenuItem()
        mainMenu.addItem(appItem)
        let appMenu = NSMenu()
        appItem.submenu = appMenu
        appMenu.addItem(withTitle: "About " + appName,
                        action: #selector(NSApplication.orderFrontStandardAboutPanel(_:)), keyEquivalent: "")
        appMenu.addItem(NSMenuItem.separator())
        appMenu.addItem(withTitle: "Hide " + appName, action: #selector(NSApplication.hide(_:)), keyEquivalent: "h")
        appMenu.addItem(NSMenuItem.separator())
        appMenu.addItem(withTitle: "Quit " + appName, action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")

        let editItem = NSMenuItem()
        mainMenu.addItem(editItem)
        let editMenu = NSMenu(title: "Edit")
        editItem.submenu = editMenu
        editMenu.addItem(withTitle: "Copy", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
        editMenu.addItem(withTitle: "Select All", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")

        let viewItem = NSMenuItem()
        mainMenu.addItem(viewItem)
        let viewMenu = NSMenu(title: "View")
        viewItem.submenu = viewMenu
        let reload = NSMenuItem(title: "Reload Book", action: #selector(reloadBook), keyEquivalent: "r")
        reload.target = self
        viewMenu.addItem(reload)
        let full = NSMenuItem(title: "Enter Full Screen",
                              action: #selector(NSWindow.toggleFullScreen(_:)), keyEquivalent: "f")
        full.keyEquivalentModifierMask = [.command, .control]
        viewMenu.addItem(full)

        let windowItem = NSMenuItem()
        mainMenu.addItem(windowItem)
        let windowMenu = NSMenu(title: "Window")
        windowItem.submenu = windowMenu
        windowMenu.addItem(withTitle: "Minimize", action: #selector(NSWindow.performMiniaturize(_:)), keyEquivalent: "m")
        NSApp.windowsMenu = windowMenu
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()
