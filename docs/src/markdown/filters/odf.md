# ODF

## Usage

The ODF filter provides support for the Open Document Format. It supports documents (`odt`), spreadsheets (`ods`), and presentations (`odp`). It also supports their flat format as well: `fodt`, `fods`, and `fodp`. In general, it will return one chunk containing all the checkable strings in the file. In the case of presentations, it will actually send multiple chunks, one for each slide.

```yaml
- name: odf
  sources:
  - '**/*.{odt,fodt,ods,odp}'
  pipeline:
  - pyspelling.filters.odf:
```

## Options

There are currently no additional options when using the ODF filter.

## Categories

HTML returns text with the following categories.

Category      | Description
------------- | -----------
`odt-content` | Text captured from document files.
`odp-content` | Text captured from presentation files.
`ods-content` | Text captured from spreadsheet files.
