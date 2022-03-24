# This is to be used to quickly format files+md5 lists into something that can be imported by csv-sql
# find . -name "*csv" -exec md5 {} \;
# perl formatmd5.pl < md5files.txt > md5files.csv


while (<STDIN>) {
        if (m|\((.+)\) = ([\da-z]{32})| ) {
                print "$1|$2\n";
        }
}
