# Handy Logic Doodahs-Short Truth Tables
## Authors
2016:
Matt Peveler

## About
This is a flask app (with a python module backing it) that can be used to solve a Short Truth Table for any number of given logical formulas and one goal. This is part of the handy logic doodahs series of Automated Theorem Provers.

![Flask App](https://raw.githubusercontent.com/MasterOdin/ShortTruthTables/master/static/screenshot.png)

It uses a functional format for inputting logical formulas. This is the base identity for inputs:
```
A
not(A)
and(A, B)
or(A, B)
if(A, B)
iff(A, B)
```
where `A` and `B` can either be atomic statements or a functional operator. All operators are either unary (not) or binary (and, or, if, iff) and there is no support for a generalized notation. This means that ```and(A, B, C)``` will thrown an error.
