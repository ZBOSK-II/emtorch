JSON Schema of the configuration, for editors supporting it in TOML files.

  $ emtorch config-schema | head -n 3
  {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "emtorch experiment configuration",

  $ emtorch config-schema --output schema.json
  $ emtorch config-schema | cmp - schema.json
