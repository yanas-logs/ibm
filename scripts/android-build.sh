#!/usr/bin/env bash
# ============================================================
#  android-build.sh - Mantra Android Build Script
#  Penggunaan:
#    ./scripts/android-build.sh          # release build
#    ./scripts/android-build.sh debug    # debug build
# ============================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; NC='\033[0m'
info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
die()   { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MOBILE_DIR="$PROJECT_ROOT/packages/mobile"
GRADLE_VERSION="8.7"
GRADLE_URL="https\\://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip"
BUILD_MODE="${1:-release}"

# ─── 1. JAVA_HOME ────────────────────────────────────────────
info "Mengkonfigurasi JAVA_HOME..."
if [ -z "${JAVA_HOME:-}" ]; then
  JAVA_HOME=$(ls -d /usr/lib/jvm/java-*-openjdk-* 2>/dev/null | sort -V | tail -1)
  [ -z "$JAVA_HOME" ] && die "Java not found. Install: sudo apt install openjdk-17-jdk"
  export JAVA_HOME
fi
export PATH="$JAVA_HOME/bin:$PATH"
ok "JAVA_HOME = $JAVA_HOME"

# ─── 2. ANDROID_HOME ─────────────────────────────────────────
info "Mengkonfigurasi ANDROID_HOME..."
if [ -z "${ANDROID_HOME:-}" ]; then
  for c in "$HOME/Android/sdk" "$HOME/Android/Sdk" "/opt/android-sdk"; do
    [ -d "$c" ] && { export ANDROID_HOME="$c"; break; }
  done
  [ -z "${ANDROID_HOME:-}" ] && die "Android SDK not found. Set ANDROID_HOME manual."
fi
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export PATH="$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$HOME/.cargo/bin:$PATH"
ok "ANDROID_HOME = $ANDROID_HOME"

# ─── 3. Force gradle-wrapper.properties ke 8.7 ───────────────
info "Memaksa gradle-wrapper.properties ke versi ${GRADLE_VERSION}..."
for wdir in \
  "$MOBILE_DIR/gen/android/gradle/wrapper" \
  "$MOBILE_DIR/gen/android/app/gradle/wrapper"; do
  mkdir -p "$wdir"
  printf 'distributionBase=GRADLE_USER_HOME\ndistributionPath=wrapper/dists\ndistributionUrl=%s\nnetworkTimeout=10000\nvalidateDistributionUrl=true\nzipStoreBase=GRADLE_USER_HOME\nzipStorePath=wrapper/dists\n' \
    "$GRADLE_URL" > "$wdir/gradle-wrapper.properties"
  ok "  Wrote: $wdir"
done

# ─── 4. Clean up the old Gradle distribution ─────────────────────
info "Cleaning up the old Gradle distribution..."
DISTS="$HOME/.gradle/wrapper/dists"
if [ -d "$DISTS" ]; then
  for d in "$DISTS"/*/; do
    name=$(basename "$d")
    if [ "$name" != "gradle-${GRADLE_VERSION}-bin" ]; then
      warn "  Delete: $name"
      rm -rf "$d"
      ok  "  Deleted: $name"
    else
      ok  "  Maintain: $name"
    fi
  done
fi

# ─── 5. Verification dx ────────────────────────────────────────
DX_BIN="$HOME/.cargo/bin/dx"
[ -x "$DX_BIN" ] || DX_BIN=$(which dx 2>/dev/null) || die "dx tidak ditemukan. Install: cargo install dioxus-cli"
ok "dx = $("$DX_BIN" --version 2>&1)"

echo ""
info "JAVA_HOME    = $JAVA_HOME"
info "ANDROID_HOME = $ANDROID_HOME"
info "Gradle       = $GRADLE_VERSION"
info "Mode         = $BUILD_MODE"
echo ""

# ─── 6. Build ────────────────────────────────────────────────
info "Operate: dx build --platform android --${BUILD_MODE}"
cd "$MOBILE_DIR"
"$DX_BIN" build --platform android --"$BUILD_MODE" 2>&1 | tee "$PROJECT_ROOT/build-android.log"
BUILD_EXIT=${PIPESTATUS[0]}

if [ $BUILD_EXIT -eq 0 ]; then
  ok "======================================"
  ok "BUILD SUCCESSFUL!"
  ok "Log: $PROJECT_ROOT/build-android.log"
  ok "======================================"
  APK=$(find "$MOBILE_DIR" -name '*.apk' 2>/dev/null | head -1)
  [ -n "$APK" ] && ok "APK: $APK"
else
  die "Build failed (exit: $BUILD_EXIT). Lihat: $PROJECT_ROOT/build-android.log"
fi
