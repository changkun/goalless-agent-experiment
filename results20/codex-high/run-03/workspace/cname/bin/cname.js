#!/usr/bin/env node
'use strict';

const { generate } = require('../lib/generator');

function usage() {
  return `Usage: cname [options]

Generate memorable, human-friendly codenames.

Options:
  -n, --count <num>    Number of names to generate (default: 1)
  -f, --format <fmt>   Output format: short|camel|snake|kebab|title|plain (default: short)
  --no-number          Omit the numeric suffix
  -s, --seed <str>     Deterministic seed (repeats give identical output)
  -h, --help           Show this help
  -v, --version        Show version
`;
}

const VERSION = require('../package.json').version;

function parseArgv(argv) {
  const opts = { count: 1 };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    switch (arg) {
      case '-h':
      case '--help':
        opts.help = true;
        break;
      case '-v':
      case '--version':
        opts.version = true;
        break;
      case '-n':
      case '--count':
        opts.count = Number(argv[++i]);
        break;
      case '-f':
      case '--format':
        opts.format = argv[++i];
        break;
      case '-s':
      case '--seed':
        opts.seed = argv[++i];
        break;
      case '--no-number':
        opts.number = false;
        break;
      default:
        if (arg.startsWith('--count=')) opts.count = Number(arg.split('=')[1]);
        else if (arg.startsWith('--format=')) opts.format = arg.split('=')[1];
        else if (arg.startsWith('--seed=')) opts.seed = arg.split('=')[1];
        else {
          process.stderr.write(`Unknown option: ${arg}\n\n${usage()}`);
          process.exit(2);
        }
    }
  }
  return opts;
}

function main() {
  const opts = parseArgv(process.argv.slice(2));
  if (opts.help) {
    process.stdout.write(usage());
    process.exit(0);
  }
  if (opts.version) {
    process.stdout.write(VERSION + '\n');
    process.exit(0);
  }

  try {
    const names = generate(opts);
    process.stdout.write((Array.isArray(names) ? names.join('\n') : names) + '\n');
  } catch (err) {
    process.stderr.write(err.message + '\n');
    process.exit(1);
  }
}

main();
