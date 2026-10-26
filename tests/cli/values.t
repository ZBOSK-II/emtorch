Extracting values from results.

  $ printf 'count=7 size=1\n' > a.bin
  $ printf 'count=13 size=2\n' > b.bin
  $ emtorch run --config "$TESTDIR/experiment.toml" --output-prefix out a.bin b.bin > /dev/null 2>&1
  $ mv out-*.json results.json

  $ emtorch values results.json
  Case,count,size\r (esc)
  a.bin,7,1\r (esc)
  b.bin,13,2\r (esc)
  

  $ emtorch values --format text results.json
  +-------+-------+------+
  |  Case | count | size |
  +-------+-------+------+
  | a.bin |   7   |  1   |
  | b.bin |   13  |  2   |
  +-------+-------+------+

  $ emtorch values --format json results.json
  [
      [
          "Case",
          "count",
          "size"
      ],
      {
          "Case": "a.bin",
          "count": 7,
          "size": 1
      },
      {
          "Case": "b.bin",
          "count": 13,
          "size": 2
      }
  ]

Filtering values.

  $ emtorch values --include 'c.*' results.json
  Case,count\r (esc)
  a.bin,7\r (esc)
  b.bin,13\r (esc)
  

  $ emtorch values --exclude count results.json
  Case,size\r (esc)
  a.bin,1\r (esc)
  b.bin,2\r (esc)
  

Writing to a file.

  $ emtorch values --output values.csv results.json
  $ cat values.csv
  Case,count,size\r (esc)
  a.bin,7,1\r (esc)
  b.bin,13,2\r (esc)
  

Repeated cases have an iteration column.

  $ emtorch run --config "$TESTDIR/experiment.toml" --output-prefix repeated --repeats 2 a.bin > /dev/null 2>&1
  $ emtorch values repeated-*.json
  Case,Iteration,count,size\r (esc)
  a.bin,1,7,1\r (esc)
  a.bin,2,7,1\r (esc)
  

Invalid arguments.

  $ emtorch values missing.json
  ERROR: [Errno 2] No such file or directory: 'missing.json' [FileNotFoundError]
  [255]

  $ emtorch values --format yaml results.json
  usage: emtorch values [-h] [--output OUTPUT]
                        [--format {csv,text,latex,mediawiki,html,json}]
                        [--include INCLUDE] [--exclude EXCLUDE]
                        results
  emtorch values: error: argument --format: invalid choice: 'yaml' (choose from 'csv', 'text', 'latex', 'mediawiki', 'html', 'json')
  [2]
