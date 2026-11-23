Configuration validation without executing the experiment.

  $ emtorch config-check --config "$TESTDIR/experiment.toml" | sed "s|$TESTDIR/||"
  experiment.toml: OK

All errors are reported, overrides are applied before validation.

  $ emtorch config-check --config "$TESTDIR/experiment.toml" \
  >   --override setups.setup.type=nope \
  >   --override actions.process.foo=1 \
  >   --override checks.report.when=sometimes | sed "s|$TESTDIR/||"
  experiment.toml: 3 error(s) found
    setups.setup.type: Unknown subtask type 'nope'
    actions.process.foo: Unexpected keyword argument
    checks.report.when: Input should be 'always', 'never', 'once' or 'per_data'

  $ emtorch config-check --config "$TESTDIR/experiment.toml" --override actions.process.foo=1 > /dev/null
  [1]

Top level errors.

  $ emtorch config-check --config "$TESTDIR/experiment.toml" --override delays.x=1 | sed "s|$TESTDIR/||"
  experiment.toml: 1 error(s) found
    delays.x: Unexpected keyword argument

Malformed TOML is reported as an invalid configuration.

  $ printf '[actions\n' > broken.toml
  $ emtorch config-check --config broken.toml
  broken.toml: 1 error(s) found
    invalid TOML: .* (re)
  [1]

  $ printf 'a = "\xff"\n' > latin1.toml
  $ emtorch config-check --config latin1.toml
  latin1.toml: 1 error(s) found
    invalid TOML: .* (re)
  [1]

Overrides which cannot be applied are reported as errors.

  $ emtorch config-check --config "$TESTDIR/experiment.toml" --override 'setups.setup.args[5]=x' | sed "s|$TESTDIR/||"
  experiment.toml: 1 error(s) found
    setups.setup.args[5]: cannot apply overrides, list index out of range

Values not supported by overrides handling are not blamed on the overrides.

  $ printf 'd = 1979-05-27\n' > date.toml
  $ emtorch config-check --config date.toml --override delays.between_cases=1
  date.toml: 1 error(s) found
    d: cannot apply overrides, Value 'date' is not a supported primitive type
  [1]

Missing configuration file.

  $ emtorch config-check --config missing.toml
  ERROR: [Errno 2] No such file or directory: 'missing.toml' [FileNotFoundError]
  [255]
