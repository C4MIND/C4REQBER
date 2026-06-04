----------------------------- MODULE C4 -----------------------------
(* TLA+ specification of C4-META cognitive architecture *)
(* Theorem 11: shortest path <= 6 steps in Z_3^3                      *)

CONSTANTS States, Operators
VARIABLES current_state, history

State == [t: {0,1,2}, s: {0,1,2}, a: {0,1,2}]
States == [t: {0,1,2}, s: {0,1,2}, a: {0,1,2}]

Init == current_state = [t |-> 0, s |-> 0, a |-> 0] /\ history = <<>>

Reachable(s1, s2) ==
    \/ /\ s2.t = s1.t + 1 /\ s2.t <= 2 /\ s2.s = s1.s /\ s2.a = s1.a
    \/ /\ s2.t = s1.t - 1 /\ s2.t >= 0 /\ s2.s = s1.s /\ s2.a = s1.a
    \/ /\ s2.s = s1.s + 1 /\ s2.s <= 2 /\ s2.t = s1.t /\ s2.a = s1.a
    \/ /\ s2.s = s1.s - 1 /\ s2.s >= 0 /\ s2.t = s1.t /\ s2.a = s1.a
    \/ /\ s2.a = s1.a + 1 /\ s2.a <= 2 /\ s2.t = s1.t /\ s2.s = s1.s
    \/ /\ s2.a = s1.a - 1 /\ s2.a >= 0 /\ s2.t = s1.t /\ s2.s = s1.s

Next == \E s \in States: Reachable(current_state, s) /\ current_state' = s

Spec == Init /\ [][Next]_<<current_state, history>>

(* Theorem 11: Every state reachable from origin in <=6 steps *)
Theorem11 == \A s \in States:
    \E path \in Seq(States):
        /\ Len(path) <= 7
        /\ path[1] = [t |-> 0, s |-> 0, a |-> 0]
        /\ path[Len(path)] = s
        /\ \A i \in 1..(Len(path) - 1): Reachable(path[i], path[i+1])
=============================================================================
