from argparse import ArgumentParser
import os
import pathlib
import shutil
import io

from bs4 import BeautifulSoup


html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Collager</title>
</head>
<body>
    <h1>Collager</h1>
    <table id="collage-container">
        <tr><th>Original</th><th>Contour</th></tr>
    </table>
</body>
</html>
"""


def main(input_dir: pathlib.Path, output_dir: pathlib.Path):
    if not input_dir.exists:
        raise FileNotFoundError(f"input file {input_dir} not found")
    orig_root = input_dir / "original"
    if not orig_root.exists:
        raise FileNotFoundError(f"input file {orig_root} not found")
    contour_root = input_dir / "contour"
    if not contour_root.exists:
        raise FileNotFoundError(f"input file {contour_root} not found")

    static = output_dir / "static"
    os.makedirs(static, exist_ok=True)

    orig_dest = static / "original"
    os.makedirs(orig_dest, exist_ok=True)
    contour_dest = static / "contour"
    os.makedirs(contour_dest, exist_ok=True)

    soup = BeautifulSoup(html_template, "html.parser")
    container = soup.find("table", id="collage-container")

    for d, _, files in os.walk(orig_root):
        dirpath = pathlib.Path(d)
        relpath = dirpath.relative_to(orig_root)

        for file in files:
            contour_file = contour_root / relpath / file
            if not contour_file.exists():
                print(f"Contour file not found for {file}")
                continue

            orig_file = orig_dest / relpath / file
            os.makedirs(orig_file.parent, exist_ok=True)
            print(f"Copying {dirpath / file} to {orig_file}")

            # animated gif cannot be copied with shutil.copy (not know why)
            with open(dirpath / file, "rb") as f:
                with open(orig_file, "xb") as f2:
                    f2.write(f.read())

            contour_file = contour_dest / relpath / file
            os.makedirs(contour_file.parent, exist_ok=True)
            print(f"Copying {contour_root / relpath / file} to {contour_file}")

            with open(contour_root / relpath / file, "rb") as f:
                with open(contour_file, "xb") as f2:
                    f2.write(f.read())

            row = soup.new_tag("tr")
            container.append(row)

            orig_cell = soup.new_tag("td")
            row.append(orig_cell)
            img_orig = soup.new_tag("img", src=str(orig_file.relative_to(output_dir)))
            orig_cell.append(img_orig)

            contour_cell = soup.new_tag("td")
            row.append(contour_cell)
            img_contour = soup.new_tag(
                "img", src=str(contour_file.relative_to(output_dir))
            )
            contour_cell.append(img_contour)

    with open(output_dir / "index.html", "w") as f:
        f.write(str(soup))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--input", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)

    args = parser.parse_args()
    main(input_dir=args.input, output_dir=args.output)
