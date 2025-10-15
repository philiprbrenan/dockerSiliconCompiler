#!/usr/bin/perl -I/home/phil/perl/cpan/DataTableText/lib/ -I/home/phil/perl/cpan/GitHubCrud/lib/
#-------------------------------------------------------------------------------
# Use silicon compiler via a docker image to place one design in another
# Philip R Brenan at gmail dot com, Appa Apps Ltd Inc., 2025
#-------------------------------------------------------------------------------
use v5.38;
use warnings FATAL => qw(all);
use strict;
use Carp;
use Data::Dump qw(dump);
use Data::Table::Text qw(:all);
use GitHub::Crud qw(:all);

my $repo    = q(dockerSiliconCompiler);                                         # Repo
my $user    = q(philiprbrenan);                                                 # User
my $home    = q(/home/phil/btreeAsm/siliconCompiler);                           # Home folder
my $wf      = q(.github/workflows/run.yml);                                     # Work flow on Ubuntu
my $docker  = "ghcr.io/philiprbrenan/sc-asic:latest";                           # Silicon compiler in a container
my $shaFile = fpe $home, q(sha);                                                # Sh256 file sums for each known file to detect changes
my @ext     = qw(.md .pl .py);                                                  # Extensions of files to upload to github

say STDERR timeStamp,  "Push to github $repo";

my @files = searchDirectoryTreesForMatchingFiles($home, @ext);                  # Files to upload
   @files = changedFiles $shaFile, @files;                                      # Filter out files that have not changed

if (!@files)                                                                    # No new files
 {say "Everything up to date";
  exit;
 }

if  (1)                                                                         # Upload via github crud
 {for my $s(@files)                                                             # Upload each selected file
   {my $c = readBinaryFile $s;                                                  # Load file

    $c = expandWellKnownWordsAsUrlsInMdFormat $c if $s =~ m(README);            # Expand README

    my $t = swapFilePrefix $s, $home;                                           # File on github
    my $w = writeFileUsingSavedToken($user, $repo, $t, $c);                     # Write file into github
    lll "$w  $t";
   }
 }

my $dt    = dateTimeStamp;
my $yml   = <<"END";                                                            # Create workflow
# Test $dt

name: Test
run-name: $repo

on:
  push:
    paths:
      - '**/run.yml'

jobs:

  test:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout\@v4

    - name: Code to execute in the docker container to place one synthesized module in another
      run: |
      cat <<EOF > exec.sh
export PATH=/root/.local/bin:\$PATH
source /app/sc/bin/activate
cd /workspace/verilog
python3 top.py
EOF
    - name: Run Silicon compiler in a docker container
      run: |
        docker run --rm -v ".:/workspace/verilog" $docker bash -c "bash /workspace/verilog/top.exec"
END

my $f = writeFileUsingSavedToken $user, $repo, $wf, $yml;                       # Upload workflow
lll "$f  Ubuntu work flow for $repo";
