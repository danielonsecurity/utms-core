(defunit day
  (length (fn [[_ None]] (* 1 86400)))  ; Duration of a day in seconds
  (timezone (fn [[_ None]] 3600))  ; UTC+1 timezone
  ;; (timezone 0)  ; UTC+1 timezone
  (start (fn [ts]
           (round
	     (- ts
	        (%
	          (+ ts
		     (self.timezone))
	          (self.length)))))))  ; Midnight calculation



(defunit week7
  (length (* 7 (day.length)))
  ;; offsets for week start:
  ;; 0 - Thursday (1970-01-01 was thursday)
  ;; 1 - Friday
  ;; 2 - Saturday
  ;; 3 - Sunday
  ;; 4 - Monday
  ;; 5 - Tuesday
  ;; 6 - Wednesday
  (offset 4)
  (timezone day.timezone)
  (start
    (fn [ts]
      (let [
            ;; _ (print "ts=" ts)
            ;; _ (print "self=" self)
            ;; _ (print "locals=" (locals))
            ;; test (breakpoint)

            day-offset (get_day_of_week ts self day)
            week-start-timestamp (- (day.start ts) (* day-offset (day.length ts)))]
        week-start-timestamp
        ))
    )
  (names ["Monday" "Tuesday" "Wednesday" "Thursday" "Friday" "Saturday" "Sunday"])
  )


(defunit week7sunday
  (length (* 7 (day.length)))
  (timezone day.timezone)
  ;; offsets for week start:
  ;; 0 - Thursday (1970-01-01 was thursday)
  ;; 1 - Friday
  ;; 2 - Saturday
  ;; 3 - Sunday
  ;; 4 - Monday
  ;; 5 - Tuesday
  ;; 6 - Wednesday
  (offset 3)
  (start
    (fn [ts]
      (let [day-offset (get_day_of_week ts self day)
            week-start-timestamp (- (day.start ts) (* day-offset (day.length ts)))]
        week-start-timestamp
        ))
   )
  (names ["Sunday" "Monday" "Tuesday" "Wednesday" "Thursday" "Friday" "Saturday"])
  )


(defunit week10
  (length (* 10 (day.length)))
  (timezone day.timezone)
  (offset 3)
  (start
    (fn [ts]
      (let [day-offset (get_day_of_week ts self day)
            week-start-timestamp (- (day.start ts) (* day-offset (day.length ts)))]
        week-start-timestamp
        ))
   )
  (names ["Firstday" "Secondday" "Thirdday" "Fourthday" "Fifthtday" "Sixthday" "Sevenday" "Eigthday" "Nineday" "Tenday"])
  )

(defunit month
  (timezone day.timezone)
  (length
    (fn [ts #* _]
      (let [timezone (datetime.timezone (datetime.timedelta :seconds (day.timezone ts)))
            now (datetime.datetime.fromtimestamp ts :tz timezone)
            year now.year
            month now.month
            leap-year? (or
                         (and (= (% year 4) 0) (!= (% year 100) 0))
                         (= (% year 400) 0))
            ;; Determine the number of days in the month
            days-in-month
            (if (in month [1 3 5 7 8 10 12])
              31
              (if (in month [4 6 9 11])
                  30
                  ;; Handle February
                  (if leap-year?
                      29  ; Leap year February
                      28)))
                                ; Non-leap year February
            ;; Calculate the month length in seconds
            month-length (* days-in-month (day.length ts))]
        month-length)))
  (start
    (fn [ts  #* _]
      (let [timezone (datetime.timezone (datetime.timedelta :seconds (day.timezone ts)))
            now (datetime.datetime.fromtimestamp ts :tz timezone)
            midnight-timestamp (.timestamp (datetime.datetime now.year now.month 1 :tzinfo timezone))]
        midnight-timestamp))))



(defunit year
  (timezone day.timezone)
  (length
    (fn [ts]
      (let [timezone (datetime.timezone (datetime.timedelta :seconds (day.timezone)))
	    current-date (datetime.datetime.fromtimestamp ts :tz timezone)
            next-year (datetime.datetime (+ current-date.year 1) 1 1 :tzinfo timezone)
            this-year (datetime.datetime current-date.year 1 1 :tzinfo timezone)
	    year-length (- (.timestamp next-year)
                           (.timestamp this-year)
                           )
            ]
        year-length
        ))
     )
  (start
   (fn [ts]
     (let [timezone (datetime.timezone (datetime.timedelta :seconds (day.timezone)))
           current-date (datetime.datetime.fromtimestamp ts :tz timezone)
           year-start (.timestamp (datetime.datetime current-date.year 1 1 :tzinfo timezone))]
       year-start
       )))

  (names ["January" "February" "March" "April" "May" "June" "July" "August" "September" "October" "November" "December" "Intercallary"])
  (index (fn [ts]
           (let [timezone (datetime.timezone (datetime.timedelta :seconds (day.timezone)))
                 current-date (datetime.datetime.fromtimestamp ts :tz timezone)]
             (- current-date.month 1)
             ))
         )
  )

(defcalendar gregorian
  (day day)
  (week week7)
  (month month)
  (year year)
  (day-of-week
    (fn [ts]
      (let [day-length (day.length ts)
            week-length week.length
            timezone-offset (day.timezone ts)
            reference (+ 0 (* (. week offset) day-length) (- timezone-offset))
            days-elapsed (// (- ts reference) day-length)
            days-per-week (// week-length day-length)
            ]
        (int (% days-elapsed days-per-week)))))
  )


(defcalendar gregorian-sunday
  (day day)
  (week week7sunday)
  (month month)
  (year year))

(defcalendar week10
  (day day)
  (week week10)
  (month month)
  (year year))


(defunit week7fixed
  (length (* 7 (day.length)))
  (offset 4)
  (timezone day.timezone)
  (start
    (fn [ts]
      (let [
            timezone (datetime.timezone (datetime.timedelta :seconds (day.timezone ts)))
            now (datetime.datetime.fromtimestamp ts :tz timezone)
            year now.year
            year-start (.timestamp (datetime.datetime year 1 1 :tzinfo timezone))
            day-length (day.length ts)
            days-elapsed (int (/ (- ts year-start) day-length))
            leap-year? (or
                         (and (= (% year 4) 0) (!= (% year 100) 0))
                         (= (% year 400) 0))
            is-leap-day (= days-elapsed 168)
            is-year-day (= days-elapsed (if leap-year? 365 364))
            week-start-timestamp (if (or is-leap-day is-year-day)
                                     ts
                                     (let [day-offset (get_day_of_week ts self day)]
                                       (- (day.start ts) (* day-offset (day.length ts)))
                                       ))
            ]
        week-start-timestamp
        ))
    )
  (names ["Monday" "Tuesday" "Wednesday" "Thursday" "Friday" "Saturday" "Sunday"])
  )



(defunit monthfixed
  (timezone day.timezone)
  (length
    (fn [ts [month-index None]]
      (let [timezone (datetime.timezone (datetime.timedelta :seconds (day.timezone ts)))
            now (datetime.datetime.fromtimestamp ts :tz timezone)
            year now.year
            day-length (day.length ts)
            ;; _ (print "MONTH INDEX:" month-index)



            ; Calculate year boundaries
            year-start (.timestamp (datetime.datetime year 1 1 :tzinfo timezone))
            days-elapsed (int (/ (- ts year-start) day-length))

            leap-year? (or
                         (and (= (% year 4) 0) (!= (% year 100) 0))
                         (= (% year 400) 0))
            ;; _ (print "Length calculation:")
            ;; _ (print "  ts:" ts)
            ;; _ (print "  year-start:" year-start)
            ;; _ (print "  leap_year:" leap-year?)
            ;; _ (print "  month-index:" month-index)


                                ; Calculate length based on either month-index or timestamp
            month-length (if (is None month-index)
                                ; When no month-index, use days_elapsed
                             (cond
                               (< days-elapsed 168) (* 28 day-length)
                               (= days-elapsed 168) (* 28 day-length) ; Always return 28 days for timestamp at Leap Day position
                               (< days-elapsed 364) (* 28 day-length)
                               (= days-elapsed 364) day-length
                               True 0)
                                ; When month-index is provided, use it for display logic
                             (cond
                               (= month-index 7) (if leap-year? day-length 0) ; Leap Day
                               (= month-index 14) day-length ; Year Day
                               (> month-index 14) 0 ; Nothing after Year Day
                               True (* 28 day-length)))

            ]
            ;; _ (print "  month_length:" month-length)

        month-length)))
  (start
    (fn [ts]
      (let [timezone (datetime.timezone (datetime.timedelta :seconds (day.timezone ts)))
            now (datetime.datetime.fromtimestamp ts :tz timezone)
            year now.year
            day-length (day.length ts)
            year-start (.timestamp (datetime.datetime year 1 1 :tzinfo timezone))
            days-elapsed (int (/ (- ts year-start) day-length))
            leap-year? (or
                         (and (= (% year 4) 0) (!= (% year 100) 0))
                         (= (% year 400) 0))

            ;; _ (print "Start calculation:")
            ;; _ (print "  ts:" ts)
            ;; _ (print "  days_elapsed:" days-elapsed)
            month-start (cond
                                ; First 6 months (0-167 days)
                          (< days-elapsed 168)
                          (+ year-start (* (int (/ days-elapsed 28)) (* 28 day-length)))

                                ; Leap Day (day 168)
                          (= days-elapsed 168)
                          (+ year-start (* 168 day-length))

                                ; Regular months after Leap Day (169-363/364)
                          (< days-elapsed 364)
                          (+ year-start
                             (if leap-year? (* 169 day-length) (* 168 day-length))
                             (* (int (/ (- days-elapsed (if leap-year? 169 168)) 28)) (* 28 day-length)))

                          True
                          (+ year-start (* 364 day-length)))]
        ;; _ (print "  month-start:" month-start)
        month-start))))



(defunit yearfixed
  (timezone day.timezone)
  (length
    (fn [ts]
      (let [
            timezone (datetime.timezone (datetime.timedelta :seconds (day.timezone)))
	    now (datetime.datetime.fromtimestamp ts :tz timezone)
            year now.year
            leap-year? (or
                         (and (= (% year 4) 0) (!= (% year 100) 0))
                         (= (% year 400) 0))
            day-length (day.length ts)
            year-length (if leap-year?
                            (* 366 day-length)
                            (* 365 day-length))
            ]
        year-length
        ))
     )
  (start
   (fn [ts]
     (let [timezone (datetime.timezone (datetime.timedelta :seconds (day.timezone)))
           current-date (datetime.datetime.fromtimestamp ts :tz timezone)
           year-start (.timestamp (datetime.datetime current-date.year 1 1 :tzinfo timezone))]
       year-start
       )))

  (names ["January" "February" "March" "April" "May" "June" "Leap Day" "Sol" "July" "August" "September" "October" "November" "December" "Year Day"])
  (index (fn [ts]
           (let [timezone (datetime.timezone (datetime.timedelta :seconds (day.timezone)))
                 now (datetime.datetime.fromtimestamp ts :tz timezone)
                 year now.year
                 year-start (.timestamp (datetime.datetime year 1 1 :tzinfo timezone))
                 day-length (day.length ts)
                 days-elapsed (int (/ (- ts year-start) day-length))
                 leap-year? (or
                              (and (= (% year 4) 0) (!= (% year 100) 0))
                              (= (% year 400) 0))

                 month-index (cond
                                ; First 6 months
                               (< days-elapsed 168) (int (/ days-elapsed 28))
                                ; Leap Day
                               (= days-elapsed 168) 6  ; Index for "Leap Day"
                                ; After Leap Day
                               (< days-elapsed (if leap-year? 365 364))
                               (+ 7 (int (/ (- days-elapsed (if leap-year? 169 168)) 28)))
                                ; Year Day
                               True 14)

                 ]
             month-index
             ))
         )
  )


(defcalendar ifc
  (day day)
  (week week7fixed)
  (month monthfixed)
  (year yearfixed)
  (day-of-week
    (fn [ts]
      (let [day-length (day.length ts)
            week-length week.length
            timezone-offset (day.timezone ts)
            reference (+ 0 (* (. week offset) day-length) (- timezone-offset))
            ;; year-start (year.get_value "start" ts)
            ;; heres-what-i-need-to-debug-please ((. year heres-what-i-need-to-debug-please) ts)
            days-elapsed (// (- ts reference) day-length)
            days-per-week (// week-length day-length)
            ]
        ;; (print year-start)
        (int (% days-elapsed days-per-week)))))

  )
