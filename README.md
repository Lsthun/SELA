# SELA Website

Standalone static website project for Sela Construction, LLC.

## Structure

- `index.html` contains the page markup for the published site.
- `home.html` redirects to `index.html` for compatibility.
- `home.css` contains the styling.
- `assets/` contains the logo, photography, and service area graphic.

## Local use

Open `index.html` directly in a browser, or serve the folder with any static file server.

Example:

```bash
cd /Users/sharifkharuf/Documents/SELA
python3 -m http.server 5101
```

Then open `http://127.0.0.1:5101/`.

## Notes

This project has no Flask app, build step, or server-side runtime.
The reviews section is currently a static placeholder and can be replaced later with approved review content.