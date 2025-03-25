(def-event TEST-EVENT
  (name "Test Complex Event")
  (state "TODO")                    ; user-defined state
  (tags ["test" "example" "demo"])  ; list of tags

  ;; Time specifications (all timestamps in seconds since epoch)
  (schedule 1738939200)            ; scheduled for specific time
  (deadline 1739025600)            ; due by specific time
  (timestamp 1738852800)           ; point in time
  (timerange {:start 1738939200    ; time range (from-to)
              :end 1739025600})

  ;; Clock entries (list of [start end] timestamps)
  (clock-entries [
    [1738852800 1738856400]        ; completed entry
    [1738939200 None]              ; ongoing entry
  ])

  ;; Additional properties
  (properties {
    :priority "A"
    :location "Office"
    :url "https://example.com"
    :notes "This is a test event with all possible fields"
  }))
