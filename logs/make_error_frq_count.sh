grep 'Description:' xmlwf_errs.txt | cut -d':' -f2 | sort | uniq -c | sort -nr > xmlwf_err_cnt.txt
