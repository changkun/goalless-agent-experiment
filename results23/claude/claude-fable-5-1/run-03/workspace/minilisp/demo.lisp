;; A few small programs to show minilisp working.

(define (range a b)
  (if (>= a b) '() (cons a (range (+ a 1) b))))

(define (filter p l)
  (cond ((null? l) '())
        ((p (car l)) (cons (car l) (filter p (cdr l))))
        (else (filter p (cdr l)))))

(define (foldl f acc l)
  (if (null? l) acc (foldl f (f acc (car l)) (cdr l))))

;; Sieve of Eratosthenes
(define (sieve l)
  (if (null? l) '()
      (let ((p (car l)))
        (cons p (sieve (filter (lambda (x) (not (= 0 (modulo x p)))) (cdr l)))))))

(display "primes below 60: " (sieve (range 2 60))) (newline)

;; Tail-recursive sum over a big range, no stack growth
(define (sum-to n)
  (define (go i acc) (if (> i n) acc (go (+ i 1) (+ acc i))))
  (go 1 0))
(display "sum 1..200000 = " (sum-to 200000)) (newline)

;; Closures as objects
(define (make-account balance)
  (lambda (op amount)
    (cond ((eq? op 'deposit) (set! balance (+ balance amount)) balance)
          ((eq? op 'withdraw)
           (if (> amount balance) (error "insufficient funds")
               (begin (set! balance (- balance amount)) balance)))
          (else (error "unknown op" op)))))
(define acct (make-account 100))
(acct 'deposit 50)
(display "balance after deposit 50, withdraw 30: " (acct 'withdraw 30)) (newline)

;; Church numerals, because why not
(define zero (lambda (f) (lambda (x) x)))
(define (succ n) (lambda (f) (lambda (x) (f ((n f) x)))))
(define (church->int n) ((n (lambda (k) (+ k 1))) 0))
(define three (succ (succ (succ zero))))
(define (add m n) (lambda (f) (lambda (x) ((m f) ((n f) x)))))
(display "church 3+3 = " (church->int (add three three))) (newline)

(display "fold product of 1..10 = " (foldl * 1 (range 1 11))) (newline)
