# CHANGELOG.md
## [0.1.0.1] 2025-09-08
 - Added previews for:
  - Video thumbnail previews with icat
  - Epub, mobi
  - Torrent files
  - Code files with syntax highlighting
  - Directories
 - Added colour highlights to distingiush directories and files.

## [0.1.0.0] 2025-09-07
 - Created FileManager class.
 - Added support for displaying images using icat and ueberzugpp (the latter still has problems).
 - Added side pane to display file info.
 - Data is now generated using the asynchronous, multithreaded Picker generate_picker_data() function.
   - Much faster and allows the Picker to load instantly as the file attributes are determined in the background.
