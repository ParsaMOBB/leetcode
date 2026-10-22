# Intuition
Rotating and reversing an array feels like shuffling things around,
but **neither operation ever changes which elements are next to each other.**

So think of the array as a **necklace** 📿:

- the beads sit on a circle and **never move**,
- a clasp `#` marks where we start reading,
- an arrow shows which way we read (↻ clockwise or ↺ counter-clockwise).

Now both operations become tiny:

| Operation | What it does to the array | What it does to the necklace |
|---|---|---|
| 🔄 **Rotate Left** | first element jumps to the end | the clasp `#` slides **one bead forward** in the reading direction |
| 🔁 **Reverse** | the array is read backwards | the arrow **flips**; the clasp stays where it is |

![Necklace intro](https://raw.githubusercontent.com/ParsaMOBB/leetcode-necklace-solution/main/images/intro.gif)

Watch the colored array at the bottom: it changes on every move, but the necklace never does.

# Approach
### Step 1: Is it even possible? 🤔

The beads never move, so the only arrays we can ever reach come from **reading this same necklace** from some clasp position in some direction.

`[0, 1, …, n-1]` is a necklace where every bead's neighbours differ by exactly 1 (with `n-1` touching `0`).
So **our** necklace has to look exactly like that too, read either ↻ or ↺.

![Valid vs invalid necklace](https://raw.githubusercontent.com/ParsaMOBB/leetcode-necklace-solution/main/images/valid_vs_invalid.png)

In code: rotate `nums` so that `0` comes first. Then the array must be either

- `0, 1, 2, …, n-1`: the necklace reads correctly **↻ clockwise**, or
- `0, n-1, n-2, …, 1`: the necklace reads correctly **↺ counter-clockwise** (we detect this from `nums[1] == n-1`, then un-reverse it before checking).

Anything else gives `-1`.

### Step 2: Count the moves 🧮

We have to end with:
1. the clasp sitting **right in front of bead `0`**, and
2. the arrow pointing the way the necklace reads `0 → 1 → 2 → …`.

The clasp can only walk forward, and each flip costs 1 operation, so there are only two routes worth trying. Here they race on `nums = [2,3,4,5,6,7,0,1]`:

![Two routes race](https://raw.githubusercontent.com/ParsaMOBB/leetcode-necklace-solution/main/images/routes.gif)

Let $p$ be the index of `0` in the original `nums`.

| The necklace reads correctly… | Route A | Route B | Answer |
|---|---|---|---|
| ↻ (same as our arrow) | walk $p$ beads | flip, walk $n-p$ back, flip | $\min(p,\ n-p+2)$ |
| ↺ (opposite to our arrow) | walk $p+1$ beads, flip | flip, walk $n-p-1$ | $\min(p+2,\ n-p)$ |

These are exactly the two `return` lines in the code. ✨

### Step 3: Watch the examples 🎬

**Example 1:** `[0,2,1]` → Rotate, Reverse → **2**

![Example 1](https://raw.githubusercontent.com/ParsaMOBB/leetcode-necklace-solution/main/images/example1.gif)

**Example 2:** `[1,0,2]` → Reverse, Rotate → **2**

![Example 2](https://raw.githubusercontent.com/ParsaMOBB/leetcode-necklace-solution/main/images/example2.gif)

### Edge cases ⚠️

- $n \le 1$: already sorted, so the answer is `0`.
- $n = 2$: a 2-bead necklace reads the same both ways, so the ↻/↺ check is ambiguous (`nums[1] == n-1` is true even for `[0,1]`). The answer is just `1` if `nums = [1,0]`, else `0`.

# Complexity
- Time complexity: $$O(n)$$
One scan to find `0`, plus a constant number of `rotate` / `reverse` / `is_sorted` passes.

- Space complexity: $$O(1)$$
Everything happens in place.

# Code
```cpp []
/**
 * Think of the array as a necklace, with a '#' marking the reading point.
 *
 * Each operation can be interpreted as follows:
 * 1. Reverse the array: Reverse the reading direction of the necklace
 *    (from clockwise to counterclockwise, or vice versa).
 * 2. Rotate left by one: Move the '#' one position forward in the
 *    current reading direction.
 */
class Solution {
public:
    int minOperations(vector<int>& nums) {
        int n = nums.size();

        if (n <= 1)
            return 0;

        if (n == 2) {
            return nums[0] == 1;
        }

        int pos_zero = -1;
        for (int i = 0; i < n; i++)
            if (nums[i] == 0)
                pos_zero = i;

        rotate(nums.begin(), nums.begin() + pos_zero, nums.end());

        bool reversed = 0;
        if (nums[1] == n - 1) {
            reversed = 1;
            rotate(nums.begin(), nums.begin() + 1, nums.end());
            reverse(nums.begin(), nums.end());
        }

        if (!std::is_sorted(nums.begin(), nums.end()))
            return -1;

        if (reversed) {
            return min(pos_zero + 2, n - pos_zero);
        }

        return min(pos_zero, n - pos_zero + 2);
    }
};
```
