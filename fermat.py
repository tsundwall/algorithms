from random import randrange
import math

##where the two algorithms diasgree-- the algorithms will produce different outputs when provided with
##a carmichael number, and a low value of k (high values of k will provide a high probability of true negative results for Fermat, and r!=1).
##disagreement for non-carmichael composite numbers can occur at small values of k, since false positives can still occur with
##probability 1/2^k (Fermat) and 1/4^k (MR). for this second case, i set k=1 and played around with some small composite
##numbers like 2,4, and 6. after running several trials, a few false passes occurred, especially with Fermat's

def prime_test(N, k):

    return fermat(N,k), miller_rabin(N,k)


def mod_exp(x, y, N):

    if y == 0: #typical base case
        return 1

    z = mod_exp(x, math.floor(y / 2), N) #recursively seek the modulus of square root (x^y)

    if y % 2 == 0: #if even, simply return z^2 mod n
        return z ** 2 % N

    else: #if odd, scale z^2 by x and then find the modulus
        return x * (z ** 2) % N


def fprobability(k):

    return (1 - ((1 / 2) ** k)) #return the complement of the probability of each k returning a false positive, (1/2)^K, under Fermat's

def mprobability(k):

    return (1 - ((1 / 4) ** k)) #same as above, but for a false positive under Miller-Rubin, (1/4)^K


def fermat(N,k):

    klist = [] #create array for randomly generate integers ki
    evallist = [] #create array to store all values of r

    for ki in range(1, k + 1, 1): #find k random values where 0<k<N, and add them to previously initiated list
        ki = randrange(1,N - 1)
        klist.append(ki)

    for kj in klist: #iterate through list of ki values

        sub = mod_exp(kj, N - 1, N) #call mod exp function, store r value

        if sub == 1: #store r as a binary true = 1 if r = 1
            evalk = 1

        else: #if r != 1, store as a binary false 0
            evalk = 0

        evallist.append(evalk)

    if sum(evallist) == k: #if every value in the list of results == 1, a number is prime with probability 1 - (1/2)^k
        mprobability(k) #call function to determine probability of a true prime
        return "prime"

    else:
        return "composite" #if values dont all == 1, the number is definitionally composite


def miller_rabin(N,k):

    klist = [] #init list for random ki values as with Fermat()

    for ki in range(1, k + 1, 1): #assign random values
        ki = randrange(1, N - 1)
        klist.append(ki)

    for a in klist: #iterate through k values

        sub = mod_exp(a, N - 1, N) #first, check modular exp remainder as usual

        if sub == 1 or sub == -1: #if Fermat's passes, use miller rabin to weed out carmichael numbers
            primality = modexpMRT(a, N - 1, N) #this function will return the result of successive square roots, and this variable's value will return the true primality

            if primality == "composite": #return composite if necessary
                return "composite"

        else: #no need to perform miller rabin check, number has already proven composite
            return "composite"

    mprobability(k) #if the function hasnt returned anything yet, the function is prime. check the probability that this a truly a prime

    return "prime" #once both tests have run, the fallback is that the number N is prime


def modexpMRT(x, y, N): #this is an external function that will only be called if primality needs to be proved past Fermat's

    zsqrt = y #init the base case of the while loop; this is the exponent in the modexp

    while zsqrt % 2 == 0: #the while loop will terminate when the exponent becomes odd

        zsqrt = zsqrt / 2 #divide exponent by 2

        sub = mod_exp(x, zsqrt, N) #call modexp

        if sub != 1 and sub != (N - 1): #return composite if r = 1 or -1
            return "composite"

