
if [ "$#" != 1 ]; then
    echo "Use: $0 <winsize>"
    exit 1
fi

winsize="$1"

python3 server.py -v -H 10.0.0.1 -w "$winsize"
