for f in *.bmp; do
    ffmpeg -i "$f" "${f%.bmp}.png"
done
