# OOXML

## Usage

The OOXML filter provides support for the Office Open XML format (latest format for Microsoft Office files). It supports documents (`docx`), spreadsheets (`xlsx`), and presentations (`pptx`). In general, it will return one chunk containing all the checkable strings in the file. In the case of presentations, it will actually send multiple chunks, one for each slide. Documents may return additional chunks for headers, footers, etc.

```yaml
- name: ooxml
  sources:
  - '**/*.{docx,pptx,xlsx}'
  pipeline:
  - pyspelling.filters.ooxml:
```

## Options

There are currently no additional options when using the OOXML filter.

## Categories

HTML returns text with the following categories.

Category      | Description
------------- | -----------
`docx-content` | Text captured from document files.
`pptx-content` | Text captured from presentation files.
`xlsx-content` | Text captured from spreadsheet files.
