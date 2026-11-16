#!/bin/bash
# Builds "Lalitha Sahasranama.app" into ~/Applications. Run from this folder:  bash build_app.sh
set -e
cd "$(dirname "$0")"
if ! command -v swiftc >/dev/null 2>&1; then
  echo "swiftc was not found. It comes with Xcode or the Command Line Tools (xcode-select --install)."
  exit 1
fi
APP="$HOME/Applications/Lalitha Sahasranama.app"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
swiftc -O -swift-version 5 -framework Cocoa -framework WebKit main.swift -o "$APP/Contents/MacOS/LalithaSahasranama"
cp Info.plist "$APP/Contents/Info.plist"
cp AppIcon.icns "$APP/Contents/Resources/AppIcon.icns"
cp -R book "$APP/Contents/Resources/book"
codesign --force --deep -s - "$APP" 2>/dev/null || true
echo "Built: $APP"
open "$APP"
