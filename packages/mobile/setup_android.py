#!/usr/bin/env python3
"""
Setup script for the Mantra Android build environment.
Run from within WSL: python3 packages/mobile/setup_android.py
"""
import os
import stat
import shutil

home = os.path.expanduser("~")
# __file__ is packages/mobile/setup_android.py, so go up 2 dirs for project root
project = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
mobile = os.path.join(project, "packages", "mobile")
gradle_ver = "8.7"

print("=" * 60)
print("Mantra Android Build Environment Setup")
print("=" * 60)
print(f"Project root : {project}")
print(f"Mobile dir   : {mobile}")
print(f"Gradle ver   : {gradle_ver}")
print()

# ─── 1. Create the Gradle Wrapper directory. ────────────────────────
print("[1/5] Make direktori gradle wrapper...")
wrapper_dirs = [
    os.path.join(mobile, "gen", "android", "gradle", "wrapper"),
    os.path.join(mobile, "gen", "android", "app", "gradle", "wrapper"),
    os.path.join(project, "scripts"),
]
for d in wrapper_dirs:
    os.makedirs(d, exist_ok=True)
    print(f"  mkdir: {d}")
print("  OK\n")

# ─── 2. Write gradle-wrapper.properties (version 8.7) ──────────
print("[2/5] Write gradle-wrapper.properties to version 8.7...")
wrapper_content = (
    "distributionBase=GRADLE_USER_HOME\n"
    "distributionPath=wrapper/dists\n"
    "distributionUrl=https\\://services.gradle.org/distributions/"
    f"gradle-{gradle_ver}-bin.zip\n"
    "networkTimeout=10000\n"
    "validateDistributionUrl=true\n"
    "zipStoreBase=GRADLE_USER_HOME\n"
    "zipStorePath=wrapper/dists\n"
)
for d in wrapper_dirs[:2]:  # only two gradle wrapper locations
    f = os.path.join(d, "gradle-wrapper.properties")
    with open(f, "w") as fp:
        fp.write(wrapper_content)
    print(f"  wrote: {f}")
print("  OK\n")

# ─── 3. Clean up the old Gradle distribution ─────────────────────
print("[3/5] Cleaned up the old Gradle distribution from ~/.gradle/wrapper/dists...")
dists = os.path.join(home, ".gradle", "wrapper", "dists")
if os.path.isdir(dists):
    for name in os.listdir(dists):
        full = os.path.join(dists, name)
        if not os.path.isdir(full):
            continue  # skip CACHEDIR.TAG and other files
        if name != f"gradle-{gradle_ver}-bin":
            print(f"  removing: {name}")
            shutil.rmtree(full)
            print(f"  removed:  {name}")
        else:
            print(f"  keeping:  {name}")
else:
    print(" ~/.gradle/wrapper/dists not found (will be created during build)")

# Clear version caches non-8.x
caches = os.path.join(home, ".gradle", "caches")
if os.path.isdir(caches):
    for name in os.listdir(caches):
        full = os.path.join(caches, name)
        if os.path.isdir(full) and name and name[0].isdigit() and not name.startswith("8."):
            print(f"  removing cache: {name}")
            shutil.rmtree(full)
print("  OK\n")

# ─── 4. Update ~/.bashrc ──────────────────────────────────────
print("[4/5] Configure ~/.bashrc...")
bashrc = os.path.join(home, ".bashrc")
with open(bashrc, "r") as f:
    content = f.read()

additions = []

if "JAVA_HOME" not in content:
    additions.append(
        "\n# Java Home\n"
        "export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64\n"
        "export PATH=$JAVA_HOME/bin:$PATH\n"
    )
    print("  + JAVA_HOME will be added")
else:
    print("  JAVA_HOME already available")

if "ANDROID_HOME" not in content:
    additions.append(
        "\n# Android SDK\n"
        "export ANDROID_HOME=$HOME/Android/sdk\n"
        "export ANDROID_SDK_ROOT=$ANDROID_HOME\n"
        "export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools\n"
    )
    print("  + ANDROID_HOME akan ditambahkan")
else:
    # Make sure ANDROID_SDK_ROOT is also set
    if "ANDROID_SDK_ROOT" not in content:
        additions.append(
            "\n# Android SDK Root alias\n"
            "export ANDROID_SDK_ROOT=$ANDROID_HOME\n"
        )
        print("  + ANDROID_SDK_ROOT akan ditambahkan")
    print("  ANDROID_HOME sudah ada")

if additions:
    with open(bashrc, "a") as f:
        for line in additions:
            f.write(line)
    print("  .bashrc diperbarui")

print("  OK\n")

# ─── 5. Write android-build.sh ───────────────────────────────
print("[5/5] Write scripts/android-build.sh...")
build_script = """\
#!/usr/bin/env bash
# ============================================================
#  android-build.sh - Mantra Android Build Script
#  Penggunaan:
#    ./scripts/android-build.sh          # release build
#    ./scripts/android-build.sh debug    # debug build
# ============================================================
set -euo pipefail

RED='\\033[0;31m'; GREEN='\\033[0;32m'; YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'; NC='\\033[0m'
info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
die()   { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MOBILE_DIR="$PROJECT_ROOT/packages/mobile"
GRADLE_VERSION="8.7"
GRADLE_URL="https\\\\://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip"
BUILD_MODE="${1:-release}"

# ─── 1. JAVA_HOME ────────────────────────────────────────────
info "Configure JAVA_HOME..."
if [ -z "${JAVA_HOME:-}" ]; then
  JAVA_HOME=$(ls -d /usr/lib/jvm/java-*-openjdk-* 2>/dev/null | sort -V | tail -1)
  [ -z "$JAVA_HOME" ] && die "Java not found. Install: sudo apt install openjdk-17-jdk"
  export JAVA_HOME
fi
export PATH="$JAVA_HOME/bin:$PATH"
ok "JAVA_HOME = $JAVA_HOME"

# ─── 2. ANDROID_HOME ─────────────────────────────────────────
info "Configure ANDROID_HOME..."
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
info "Force gradle-wrapper.properties to version ${GRADLE_VERSION}..."
for wdir in \\
  "$MOBILE_DIR/gen/android/gradle/wrapper" \\
  "$MOBILE_DIR/gen/android/app/gradle/wrapper"; do
  mkdir -p "$wdir"
  printf 'distributionBase=GRADLE_USER_HOME\\ndistributionPath=wrapper/dists\\ndistributionUrl=%s\\nnetworkTimeout=10000\\nvalidateDistributionUrl=true\\nzipStoreBase=GRADLE_USER_HOME\\nzipStorePath=wrapper/dists\\n' \\
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
      warn "  Menghapus: $name"
      rm -rf "$d"
      ok  "  Deleted: $name"
    else
      ok  "  Maintain: $name"
    fi
  done
fi

# ─── 5. Verification dx ────────────────────────────────────────
DX_BIN="$HOME/.cargo/bin/dx"
[ -x "$DX_BIN" ] || DX_BIN=$(which dx 2>/dev/null) || die "dx not found. Install: cargo install dioxus-cli"
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
  ok "BUILD SUCCEED!"
  ok "Log: $PROJECT_ROOT/build-android.log"
  ok "======================================"
  APK=$(find "$MOBILE_DIR" -name '*.apk' 2>/dev/null | head -1)
  [ -n "$APK" ] && ok "APK: $APK"
else
  die "Build failed (exit: $BUILD_EXIT). Look: $PROJECT_ROOT/build-android.log"
fi
"""

build_sh = os.path.join(project, "scripts", "android-build.sh")
with open(build_sh, "w") as f:
    f.write(build_script)
os.chmod(build_sh, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
print(f"  wrote: {build_sh}")
print("  OK\n")

# ─── Ringkasan ────────────────────────────────────────────────
print("=" * 60)
print("SETUP COMPLETE — Summary:")
print("=" * 60)

gw = os.path.join(mobile, "gen", "android", "gradle", "wrapper", "gradle-wrapper.properties")
print(f"\ngradle-wrapper.properties ({gw}):")
if os.path.exists(gw):
    print(open(gw).read())

dists_path = os.path.join(home, ".gradle", "wrapper", "dists")
print(f"~/.gradle/wrapper/dists/: {os.listdir(dists_path) if os.path.isdir(dists_path) else '(there isnt any yet)'}")

with open(bashrc) as f:
    bc = f.read()
print(f"\n.bashrc — JAVA_HOME set  : {'JAVA_HOME' in bc}")
print(f".bashrc — ANDROID_HOME set: {'ANDROID_HOME' in bc}")

print(f"\nScripts: {os.listdir(os.path.join(project, 'scripts'))}")
print()
print("The next step:")
print("  1. source ~/.bashrc")
print("  2. cd packages/mobile")
print("  3. ./scripts/android-build.sh")
print("     OR manual:")
print("     export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64")
print("     export ANDROID_HOME=$HOME/Android/sdk")
print("     ~/.cargo/bin/dx build --platform android --release")
