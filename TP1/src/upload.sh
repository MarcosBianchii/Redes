
if [ "$#" != 2 ]; then
    echo "Use: $0 <host> <winsize>"
    exit 1
fi

host_id="${1:1}"
winsize="$2"

python3 upload.py -v -H 10.0.0.1 -s examples -n 5MB"$host_id".bin -w "$winsize"