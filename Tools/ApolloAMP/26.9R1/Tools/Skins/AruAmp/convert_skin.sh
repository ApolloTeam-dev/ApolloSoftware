for f in *.iff; do
    ffmpeg -i "$f" "${f%.iff}.png"
done
