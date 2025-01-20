(defunit "day"
  (length (fn [[_ None]] 86400))  ; Duration of a day in seconds
  (timezone (fn [[_ None]] 3600))  ; UTC+1 timezone
  ;; (timezone 0)  ; UTC+1 timezone
  (start (fn [ts]
           (round
	     (- ts
	        (%
	          (+ ts
		     (self.timezone))
	          (self.length)))))))  ; Midnight calculation



(defunit "week7"
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


(defunit "week7sunday"
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


(defunit "week10"
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

(defunit "month"
  (timezone day.timezone)
  (length
    (fn [ts]
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
    (fn [ts]
      (let [timezone (datetime.timezone (datetime.timedelta :seconds (day.timezone ts)))
            now (datetime.datetime.fromtimestamp ts :tz timezone)
            midnight-timestamp (.timestamp (datetime.datetime now.year now.month 1 :tzinfo timezone))]
        midnight-timestamp))))



(defunit "year"
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

  (names ["January" "February" "March" "April" "May" "June" "July" "August" "September" "October" "November" "December"])
  (index (fn [ts]
           (let [timezone (datetime.timezone (datetime.timedelta :seconds (day.timezone)))
                 current-date (datetime.datetime.fromtimestamp ts :tz timezone)]
             (- current-date.month 1)
             ))
         )
  )



;; (defunit "month13"
;;     (timezone 0)
;;     (length (* day.length 28))

;;   (start
;;    (let [
;; 	timezone (datetime.timezone (datetime.timedelta :seconds self.timezone))
;; 	now (datetime.datetime.fromtimestamp TIMESTAMP :tz timezone)
;; 	midnight (datetime.datetime now.year now.month 1 :tzinfo timezone)]
;; 	(.timestamp midnight))
;;    )
;;   )



;; (defunit "month13"
;;   (length
;;     (fn [timestamp]
;;       (* 28 (day.length))
;;       ;; (let [timezone (datetime.timezone (datetime.timedelta :seconds (day.timezone)))
;;       ;;       now (datetime.datetime.fromtimestamp timestamp :tz timezone)
;;       ;;       next-month
;;       ;;       (if (= now.month 12)
;;       ;;           (datetime.datetime (+ now.year 1) 1 1)
;;       ;;           (datetime.datetime now.year (+ now.month 1) 1))
;;       ;;       month-length (- (.timestamp next-month)
;;       ;;                       (.timestamp (datetime.datetime now.year now.month 1)))]
;;       ;;   month-length)
;;       )
;;     )
;;   (start
;;     (fn [timestamp]
;;       (let [timezone (datetime.timezone (datetime.timedelta :seconds (day.timezone)))
;;             now (datetime.datetime.fromtimestamp timestamp :tz timezone)
;;             midnight-timestamp (.timestamp (datetime.datetime now.year now.month 1 :tzinfo timezone))
;;             ]
;;         midnight-timestamp)
;;       )
;;     )
;;   )


;; (defunit "myunit" (start (fn [ts] (import datetime)(.timestamp (datetime.datetime 2024 1 1)))))
                                ; Simplified


;; (defunit "test"
;;   (start
;;     (fn [timestamp]
;;       (do
;;         (import datetime)
;;         (.timestamp (datetime.datetime 2024 1 1)))
;; )))


;; (defunit "test"
;;   (length
;;    (fn [timestamp]
;;      (let [timezone (datetime.timezone (datetime.timedelta :seconds (day.timezone)))
;;            now (datetime.datetime.fromtimestamp timestamp :tz timezone)
;;            year (.year now)
;;            month (.month now)
;;            next-month-year (+ year (if (= month 12) 1 0))
;;            next-month (+ month (if (= month 12) -11 1))]
;;        (- (.timestamp (datetime.datetime next-month-year next-month 1 :tz timezone))
;;           (.timestamp (datetime.datetime year month 1 :tz timezone)))))))

;; (defunit "test"
;;   (length
;;     (fn [timestamp]
;;       (let [timezone (datetime.timezone (datetime.timedelta :seconds (day.timezone)))
;; 	    now (datetime.datetime.fromtimestamp timestamp :tz timezone)
;;             next-month
;;             (if (= now.month 12)
;;                 (datetime.datetime (+ now.year 1) 1 1)
;;                 (datetime.datetime now.year (+ now.month 1) 1))
;;             month-length (- (.timestamp next-month)
;;                             (.timestamp (datetime.datetime now.year now.month 1)))]
;;         month-length)
;;       )
;;     )
;;   )
