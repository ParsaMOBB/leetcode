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