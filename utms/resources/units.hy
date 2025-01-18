(defunit "day"
  (length (fn [[_ None]] 86400))  ; Duration of a day in seconds
  (timezone (fn [[_ None]] 0))  ; UTC+1 timezone
  ;; (timezone 0)  ; UTC+1 timezone
  (start (fn [timestamp]
           (round
	     (- timestamp
	        (%
	          (+ timestamp 
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
  (start
    (fn [timestamp]
      (let [day-offset (get_day_of_week timestamp self day)
            week-start-timestamp (- (day.start timestamp) (* day-offset (day.length timestamp)))]
        week-start-timestamp
        ))
   )
  (names ["Monday" "Tuesday" "Wednesday" "Thursday" "Friday" "Saturday" "Sunday"])
  )


(defunit "week7sunday"
  (length (* 7 (day.length)))
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
    (fn [timestamp]
      (let [day-offset (get_day_of_week timestamp self day)
            week-start-timestamp (- (day.start timestamp) (* day-offset (day.length timestamp)))]
        week-start-timestamp
        ))
   )
  (names ["Sunday" "Monday" "Tuesday" "Wednesday" "Thursday" "Friday" "Saturday"])
  )


(defunit "week10"
  (length (* 10 (day.length)))
  (offset 3)
  (start
    (fn [timestamp]
      (let [day-offset (get_day_of_week timestamp self day)
            week-start-timestamp (- (day.start timestamp) (* day-offset (day.length timestamp)))]
        week-start-timestamp
        ))
   )
  (names ["Firstday" "Secondday" "Thirdday" "Fourthday" "Fifthtday" "Sixthday" "Sevenday" "Eigthday" "Nineday" "Tenday"])
  )



(defunit "month"
  (length
    (fn [timestamp]
      (let [timezone (datetime.timezone (datetime.timedelta :seconds (day.timezone)))
	    now (datetime.datetime.fromtimestamp timestamp :tz timezone)
            next-month
            (if (= now.month 12)
                (datetime.datetime (+ now.year 1) 1 1)
                (datetime.datetime now.year (+ now.month 1) 1))
            month-length (- (.timestamp next-month)
                            (.timestamp (datetime.datetime now.year now.month 1)))]
        month-length)
      )
    )
  (start
    (fn [timestamp]
      (let [timezone (datetime.timezone (datetime.timedelta :seconds (day.timezone)))
            now (datetime.datetime.fromtimestamp timestamp :tz timezone)
            midnight-timestamp (.timestamp (datetime.datetime now.year now.month 1 :tzinfo timezone))
            ]
        midnight-timestamp)
      )
    )
  )

(defunit "year"
  (length
    (let [timezone (datetime.timezone (datetime.timedelta :seconds (day.timezone)))
	  current-date (datetime.datetime.fromtimestamp timestamp :tz timezone)
          next-year (datetime.datetime (+ current-date.year 1) 1 1 :tzinfo timezone)
          this-year (datetime.datetime current-date.year 1 1 :tzinfo timezone)
	  year-length (- (.timestamp next-year)
                         (.timestamp this-year)
                         )
          ]
      year-length
       )
     )
  (start
   (fn [timestamp]
     (let [timezone (datetime.timezone (datetime.timedelta :seconds (day.timezone)))
           current-date (datetime.datetime.fromtimestamp timestamp :tz timezone)
           year-start (.timestamp (datetime.datetime current-date.year 1 1 :tzinfo timezone))]
       year-start
       )))

  (names ["January" "February" "March" "April" "May" "June" "July" "August" "September" "October" "November" "December"])
  (index (fn [timestamp]
           (let [timezone (datetime.timezone (datetime.timedelta :seconds (day.timezone)))
                 current-date (datetime.datetime.fromtimestamp timestamp :tz timezone)]
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



