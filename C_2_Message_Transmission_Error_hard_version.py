def z_function(s):
    n = len(s)
    z = [0] * n
    l, r, k = 0, 0, 0
    for i in range(1, n):
        if i <= r:
            z[i] = min(r - i + 1, z[i - l])
        while i + z[i] < n and s[z[i]] == s[i + z[i]]:
            z[i] += 1
        if i + z[i] - 1 > r:
            l, r = i, i + z[i] - 1
    return z

def solve():
    t = input().strip()
    n = len(t)

    # Step 1: Compute the Z-function for t
    z = z_function(t)

    # Step 2: Find a valid message length
    for i in range(1, n):
        # If z[i] gives us the length of the suffix starting from i that matches the prefix
        # Check if this can be the message `s`
        if z[i] > 0 and z[i] + i == n:
            print("YES")
            print(t[:i])
            return

    # Step 3: If no such message found
    print("NO")

