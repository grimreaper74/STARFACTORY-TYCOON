import csv
import os
import sys
from PIL import Image, ImageDraw, ImageFont


def main():
    source_csv, output_dir = sys.argv[1], sys.argv[2]
    with open(source_csv, newline='', encoding='utf-8-sig') as handle:
        items = list(csv.DictReader(handle))
    os.makedirs(output_dir, exist_ok=True)
    font = ImageFont.load_default()
    columns, rows = 4, 3
    thumb_w, thumb_h, label_h = 360, 230, 34
    page_size = columns * thumb_w, rows * (thumb_h + label_h)
    for page_start in range(0, len(items), columns * rows):
        page_items = items[page_start:page_start + columns * rows]
        sheet = Image.new('RGB', page_size, (30, 32, 36))
        draw = ImageDraw.Draw(sheet)
        for index, item in enumerate(page_items):
            try:
                with Image.open(item['Path']) as image:
                    image = image.convert('RGB')
                    image.thumbnail((thumb_w - 8, thumb_h - 8), Image.Resampling.LANCZOS)
                    x = (index % columns) * thumb_w + (thumb_w - image.width) // 2
                    y = (index // columns) * (thumb_h + label_h) + (thumb_h - image.height) // 2
                    sheet.paste(image, (x, y))
            except Exception as exc:
                x = (index % columns) * thumb_w + 8
                y = (index // columns) * (thumb_h + label_h) + 8
                draw.text((x, y), f'Unreadable: {exc}', font=font, fill=(255, 110, 110))
            label = os.path.basename(item['Path']).replace('codex-clipboard-', '')[:28]
            lx = (index % columns) * thumb_w + 6
            ly = (index // columns) * (thumb_h + label_h) + thumb_h + 6
            draw.text((lx, ly), f'{page_start + index + 1:02}: {label}', font=font, fill=(235, 235, 235))
        page = page_start // (columns * rows) + 1
        sheet.save(os.path.join(output_dir, f'clipboard_index_{page:02}.jpg'), quality=88)


if __name__ == '__main__':
    main()
