xmlstarlet sel -t -v "//a/@href[starts-with(.,http)]" -n *.html | sort | uniq -c | sort -nr > logs/href_frq.txt
xmlstarlet sel -t -v "//a/@href[starts-with(.,http)]" -n *.html | sort -u > logs/href_uniq.txt
wget -nv --spider -t 1 -i logs/href_uniq.txt -o logs/href_spider_log.txt
