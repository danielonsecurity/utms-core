(def-var current-time (get-ntp-date))

(def-var current-year current-time.year)

(def-var current-month current-time.month)

(def-var current-day current-time.day)

(def-var day-start (datetime.datetime current-year current-month current-day 0 0 0 :tzinfo (get_timezone 0)))

(def-var month-start (datetime.datetime current-year current-month 1 0 0 0 :tzinfo (get_timezone 0)))

(def-var year-start (datetime.datetime current-year 1 1 0 0 0 :tzinfo (get_timezone 0)))

(def-var millenium-start (datetime.datetime 2000 1 1 0 0 0 :tzinfo (get_timezone 0)))
