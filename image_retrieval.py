import os
import requests
from bs4 import BeautifulSoup
import urllib.parse
from PIL import Image

# Für SVG-Konvertierung
try:
    from cairosvg import svg2png
    CAIROSVG_AVAILABLE = True
except ImportError:
    CAIROSVG_AVAILABLE = False
    print("Error: cairosvg not installed. Please install it to convert SVG to PNG: pip install cairosvg")
    exit()

# Output folder for downloaded images
output_folder = "wikipedia_images"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# File containing the Wikipedia URLs
path = os.getcwd()
wiki_links_file = os.path.join(path, "Wiki_Links.txt")

# Headers to mimic a browser request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def read_wiki_urls():
    """Read Wikipedia URLs from the Wiki_Links.txt file."""
    try:
        with open(wiki_links_file, "r", encoding="utf-8") as file:
            urls = [line.strip() for line in file if line.strip()]
        return urls
    except Exception as e:
        print(f"Error reading {wiki_links_file}: {e}")
        return []

def convert_to_png(image_path):
    """Convert an image (e.g., SVG) to PNG format."""
    try:
        if image_path.lower().endswith(".svg"):
            png_path = image_path.replace(".svg", ".png")
            svg2png(url=image_path, write_to=png_path, background_color="white")
            print(f"Converted SVG to PNG: {png_path}")
            # Remove the original SVG file
            os.remove(image_path)
            return png_path
        return image_path
    except Exception as e:
        print(f"Error converting {image_path} to PNG: {e}")
        return image_path

def set_white_background(image_path):
    """Set a white background for an image with transparency."""
    try:
        img = Image.open(image_path)
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            img = img.convert("RGBA")
            white_background = Image.new("RGBA", img.size, (255, 255, 255, 255))
            white_background.paste(img, (0, 0), img)
            white_background = white_background.convert("RGB")
            white_background.save(image_path, "PNG")
            print(f"Set white background for: {image_path}")
    except Exception as e:
        print(f"Error setting white background for {image_path}: {e}")

def download_image(image_url, filename):
    """Download an image from the given URL and save it to the specified filename."""
    try:
        if image_url.startswith("//"):
            image_url = "https:" + image_url
        response = requests.get(image_url, headers=headers, timeout=10)
        response.raise_for_status()
        # Ensure the filename ends with .png
        if not filename.lower().endswith(".png"):
            filename = filename.rsplit(".", 1)[0] + ".png"
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"Downloaded: {filename}")
        # Convert to PNG if necessary (e.g., for SVG)
        filename = convert_to_png(filename)
        # Set white background for the PNG
        set_white_background(filename)
    except Exception as e:
        print(f"Error downloading {image_url}: {e}")

def get_full_resolution_image(file_page_url):
    """Retrieve the full-resolution image from Wikimedia Commons."""
    try:
        response = requests.get(file_page_url, headers=headers, timeout=10)
        response.raise_for_status()
        file_soup = BeautifulSoup(response.text, "html.parser")

        # Look for the full-resolution image link
        original_link = file_soup.find("a", {"class": "internal"})
        if original_link and "href" in original_link.attrs:
            original_url = original_link["href"]
            if original_url.startswith("//"):
                original_url = "https:" + original_url
            return original_url
    except Exception as e:
        print(f"Error getting full resolution from {file_page_url}: {e}")
    return None

def get_image_url(img):
    """Extract the full-resolution image URL from Wikipedia/Wikimedia."""
    try:
        # Get parent <a> tag linking to Wikimedia file page
        parent_a = img.find_parent("a", href=True)
        if parent_a and "href" in parent_a.attrs:
            file_page_url = urllib.parse.urljoin("https://en.wikipedia.org", parent_a["href"])
            if "wikimedia.org" in file_page_url or "File:" in file_page_url:
                full_res_url = get_full_resolution_image(file_page_url)
                if full_res_url:
                    return full_res_url

        # Fallback: Extract image URL directly from <img> tag
        src = img.get("src")
        if src:
            return "https:" + src if src.startswith("//") else src

    except Exception as e:
        print(f"Error extracting image URL: {e}")
    return None

def scrape_images_from_wiki(url):
    """Scrape images from Wikipedia page and download originals."""
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        content_section = soup.find("div", id="mw-content-text")
        if not content_section:
            print(f"Main content section not found on {url}")
            return

        # Find images in content (article images + infobox images)
        images = content_section.find_all("img", class_="mw-file-element") + soup.find_all("img", class_="infobox-image")

        if not images:
            print(f"No images found in the main content section of {url}")
            return

        # Get page title for naming
        page_title = soup.find("h1", id="firstHeading").text.replace(" ", "_").replace("/", "_")

        downloaded_files = set()  # Avoid duplicate downloads

        for idx, img in enumerate(images):
            original_url = get_image_url(img)
            if not original_url:
                print(f"No valid image URL found for image {idx + 1} on {url}")
                continue

            filename = urllib.parse.unquote(original_url.split("/")[-1]).split("?")[0]
            filename = f"{page_title}_image_{idx + 1}_{filename}"
            filepath = os.path.join(output_folder, filename)

            if filename not in downloaded_files:
                download_image(original_url, filepath)
                downloaded_files.add(filename)
            else:
                print(f"Skipping duplicate: {filename}")

    except Exception as e:
        print(f"Error scraping {url}: {e}")

# Main execution
print("Starting Wikipedia image scraper...")
wiki_urls = read_wiki_urls()

if not wiki_urls:
    print("No URLs found in Wiki_Links.txt. Exiting.")
    exit()

for url in wiki_urls:
    print(f"Scraping images from {url}...")
    scrape_images_from_wiki(url)

print(f"\nDone! Check the '{output_folder}' folder for downloaded images.")