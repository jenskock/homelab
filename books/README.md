# Books

Kavita (`books.jenskock.de`) + books-processing / CWA (`books-processing.jenskock.de`).

Drop finished ebooks into the inbox → metadata/convert → `Kavita/books/books` → Kavita. Inbox files are deleted after processing.

| Host | Purpose |
| --- | --- |
| `/mnt/synology_backup/jens/ebooks/inbox` | Ingest |
| `/mnt/synology_backup/jens/ebooks/books` | Kavita mount |
| `/mnt/synology_backup/jens/ebooks/books/books` | CWA library (nested path is intentional) |
| `/opt/books` | Config + `.env` |

Default CWA login: `admin` / `admin123` — change it.
