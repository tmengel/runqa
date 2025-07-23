#!/usr/bin/perl

use strict;
use warnings;
use File::Path;
use File::Basename;
use Getopt::Long;
use DBI;

my $dbh1 = DBI->connect("dbi:ODBC:Production_write","") || die $DBI::errstr;
my $dbh2 = DBI->connect("dbi:ODBC:daq","") || die $DBI::errstr;

my $getmaxrun = $dbh1->prepare("select max(runnumber) from goodruns");
my $getnewruns = $dbh2->prepare("select distinct(runnumber) from run where runnumber > ? and runtype='physics' order by runnumber");
my $insertrun = $dbh1->prepare("insert into goodruns (runnumber) values (?)");
$getmaxrun->execute();
my $maxrun=42000;
if ($getmaxrun->rows > 0)
{
    my @res1 = $getmaxrun->fetchrow_array();
    if (defined $res1[0])
{
    $maxrun=$res1[0];
}
}
print "max runnumber: $maxrun\n";
$getnewruns->execute($maxrun);
while (my @res2 = $getnewruns->fetchrow_array())
{
    print "inserting run $res2[0] to goodruns table\n";
    $insertrun->execute($res2[0]);
}
$getnewruns->finish();
$getmaxrun->finish();
$dbh1->disconnect;
$dbh2->disconnect;
