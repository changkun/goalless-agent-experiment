import io
import unittest

import minilisp as ml
from minilisp import LispError, run, to_string


def ev(src):
    return to_string(run(src))


class ParserTests(unittest.TestCase):
    def test_atoms(self):
        self.assertEqual(ev("42"), "42")
        self.assertEqual(ev("-3.5"), "-3.5")
        self.assertEqual(ev("#t"), "#t")
        self.assertEqual(ev('"hi\\n"'), '"hi\\n"')

    def test_quote_and_lists(self):
        self.assertEqual(ev("'(1 2 (3 4) \"s\" sym)"), '(1 2 (3 4) "s" sym)')
        self.assertEqual(ev("'()"), "()")
        self.assertEqual(ev("(cons 1 2)"), "(1 . 2)")

    def test_comments(self):
        self.assertEqual(ev("; a comment\n(+ 1 2) ; trailing"), "3")

    def test_errors(self):
        for bad in ["(", ")", "(1 2", '"open']:
            with self.assertRaises(LispError):
                run(bad)


class ArithmeticTests(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(ev("(+ 1 2 3)"), "6")
        self.assertEqual(ev("(- 10 3 2)"), "5")
        self.assertEqual(ev("(- 4)"), "-4")
        self.assertEqual(ev("(* 2 3 4)"), "24")
        self.assertEqual(ev("(/ 12 4)"), "3")
        self.assertEqual(ev("(/ 1 4)"), "0.25")
        self.assertEqual(ev("(+)"), "0")
        self.assertEqual(ev("(*)"), "1")

    def test_comparisons(self):
        self.assertEqual(ev("(< 1 2 3)"), "#t")
        self.assertEqual(ev("(< 1 3 2)"), "#f")
        self.assertEqual(ev("(= 2 2.0)"), "#t")
        self.assertEqual(ev("(>= 3 3 1)"), "#t")

    def test_type_errors(self):
        with self.assertRaises(LispError):
            run("(+ 1 \"a\")")
        with self.assertRaises(LispError):
            run("(/ 1 0)")
        with self.assertRaises(LispError):
            run("(+ 1 #t)")


class SpecialFormTests(unittest.TestCase):
    def test_if(self):
        self.assertEqual(ev("(if #t 1 2)"), "1")
        self.assertEqual(ev("(if #f 1 2)"), "2")
        self.assertEqual(ev("(if '() 1 2)"), "1")  # only #f is false
        self.assertEqual(ev("(if 0 1 2)"), "1")
        self.assertEqual(ev("(if #f 1)"), "()")

    def test_define_and_set(self):
        self.assertEqual(ev("(define x 5) (set! x (+ x 1)) x"), "6")
        with self.assertRaises(LispError):
            run("(set! undefined 1)")

    def test_lambda_and_closures(self):
        src = """
        (define (make-counter)
          (let ((n 0))
            (lambda () (set! n (+ n 1)) n)))
        (define c1 (make-counter))
        (define c2 (make-counter))
        (c1) (c1)
        (list (c1) (c2))
        """
        self.assertEqual(ev(src), "(3 1)")

    def test_variadic(self):
        self.assertEqual(ev("((lambda args args) 1 2 3)"), "(1 2 3)")
        self.assertEqual(ev("((lambda (a . rest) (list a rest)) 1 2 3)"), "(1 (2 3))")
        self.assertEqual(ev("(define (f a . r) r) (f 1)"), "()")

    def test_arity_errors(self):
        with self.assertRaises(LispError):
            run("((lambda (a b) a) 1)")
        with self.assertRaises(LispError):
            run("((lambda (a) a) 1 2)")

    def test_let_cond_and_or(self):
        self.assertEqual(ev("(let ((a 1) (b 2)) (+ a b))"), "3")
        self.assertEqual(ev("(cond (#f 1) ((= 1 1) 2) (else 3))"), "2")
        self.assertEqual(ev("(cond (#f 1) (else 3))"), "3")
        self.assertEqual(ev("(cond (#f 1))"), "()")
        self.assertEqual(ev("(and 1 2 3)"), "3")
        self.assertEqual(ev("(and 1 #f 3)"), "#f")
        self.assertEqual(ev("(and)"), "#t")
        self.assertEqual(ev("(or #f 2 3)"), "2")
        self.assertEqual(ev("(or #f #f)"), "#f")
        self.assertEqual(ev("(or)"), "#f")

    def test_and_or_short_circuit(self):
        self.assertEqual(ev("(define x 0) (and #f (set! x 1)) x"), "0")
        self.assertEqual(ev("(define x 0) (or #t (set! x 1)) x"), "0")

    def test_begin(self):
        self.assertEqual(ev("(begin 1 2 3)"), "3")
        self.assertEqual(ev("(begin)"), "()")


class TailCallTests(unittest.TestCase):
    def test_deep_loop_does_not_overflow(self):
        src = """
        (define (loop i acc)
          (if (= i 0) acc (loop (- i 1) (+ acc 1))))
        (loop 100000 0)
        """
        self.assertEqual(ev(src), "100000")

    def test_mutual_recursion_in_tail_position(self):
        src = """
        (define (even? n) (if (= n 0) #t (odd? (- n 1))))
        (define (odd? n) (if (= n 0) #f (even? (- n 1))))
        (even? 50001)
        """
        self.assertEqual(ev(src), "#f")

    def test_tail_position_through_cond_and_let_and_begin(self):
        src = """
        (define (loop i)
          (cond ((= i 0) 'done)
                (else (let ((j (- i 1))) (begin (loop j))))))
        (loop 50000)
        """
        self.assertEqual(ev(src), "done")

    def test_tail_position_through_and_or(self):
        src = """
        (define (loop i) (or (= i 0) (loop (- i 1))))
        (loop 50000)
        """
        self.assertEqual(ev(src), "#t")


class ListTests(unittest.TestCase):
    def test_list_ops(self):
        self.assertEqual(ev("(car '(1 2 3))"), "1")
        self.assertEqual(ev("(cdr '(1 2 3))"), "(2 3)")
        self.assertEqual(ev("(length '(1 2 3))"), "3")
        self.assertEqual(ev("(append '(1 2) '(3) '() '(4 5))"), "(1 2 3 4 5)")
        self.assertEqual(ev("(append)"), "()")
        self.assertEqual(ev("(reverse '(1 2 3))"), "(3 2 1)")
        self.assertEqual(ev("(map (lambda (x) (* x x)) '(1 2 3))"), "(1 4 9)")
        self.assertEqual(ev("(map + '(1 2) '(10 20))"), "(11 22)")
        self.assertEqual(ev("(apply + 1 2 '(3 4))"), "10")

    def test_predicates(self):
        self.assertEqual(ev("(null? '())"), "#t")
        self.assertEqual(ev("(list? '(1 . 2))"), "#f")
        self.assertEqual(ev("(pair? '(1 . 2))"), "#t")
        self.assertEqual(ev("(symbol? 'a)"), "#t")
        self.assertEqual(ev("(string? \"a\")"), "#t")
        self.assertEqual(ev("(string? 'a)"), "#f")
        self.assertEqual(ev("(number? 1)"), "#t")
        self.assertEqual(ev("(number? #t)"), "#f")
        self.assertEqual(ev("(procedure? car)"), "#t")
        self.assertEqual(ev("(procedure? (lambda () 1))"), "#t")

    def test_equality(self):
        self.assertEqual(ev("(equal? '(1 (2 3)) '(1 (2 3)))"), "#t")
        self.assertEqual(ev("(eq? '(1) '(1))"), "#f")
        self.assertEqual(ev("(eq? 'a 'a)"), "#t")
        self.assertEqual(ev("(eqv? 2 2)"), "#t")
        self.assertEqual(ev("(equal? \"ab\" \"ab\")"), "#t")

    def test_car_of_non_pair(self):
        with self.assertRaises(LispError):
            run("(car '())")


class ProgramTests(unittest.TestCase):
    def test_factorial_and_fib(self):
        self.assertEqual(ev("(define (fact n) (if (< n 2) 1 (* n (fact (- n 1))))) (fact 20)"), "2432902008176640000")
        self.assertEqual(ev("(define (fib n) (if (< n 2) n (+ (fib (- n 1)) (fib (- n 2))))) (fib 15)"), "610")

    def test_higher_order(self):
        src = """
        (define (compose f g) (lambda (x) (f (g x))))
        (define (inc x) (+ x 1))
        (define (dbl x) (* x 2))
        ((compose inc dbl) 5)
        """
        self.assertEqual(ev(src), "11")

    def test_quicksort(self):
        src = """
        (define (filter p l)
          (cond ((null? l) '())
                ((p (car l)) (cons (car l) (filter p (cdr l))))
                (else (filter p (cdr l)))))
        (define (qs l)
          (if (null? l) '()
              (let ((p (car l)) (rest (cdr l)))
                (append (qs (filter (lambda (x) (< x p)) rest))
                        (list p)
                        (qs (filter (lambda (x) (>= x p)) rest))))))
        (qs '(3 1 4 1 5 9 2 6 5 3 5))
        """
        self.assertEqual(ev(src), "(1 1 2 3 3 4 5 5 5 6 9)")

    def test_display_output(self):
        buf = io.StringIO()
        old = ml._output
        ml._output = buf
        try:
            run('(display "x=" 1 (list 1 "a")) (newline)')
        finally:
            ml._output = old
        self.assertEqual(buf.getvalue(), 'x=1(1 "a")\n')

    def test_error_primitive(self):
        with self.assertRaises(LispError) as cm:
            run('(error "boom" 42)')
        self.assertEqual(str(cm.exception), "boom 42")

    def test_unbound(self):
        with self.assertRaises(LispError) as cm:
            run("nope")
        self.assertIn("unbound symbol: nope", str(cm.exception))

    def test_not_a_procedure(self):
        with self.assertRaises(LispError):
            run("(1 2)")


if __name__ == "__main__":
    unittest.main()
