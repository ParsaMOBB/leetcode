/**
 * This solution is O(n)
 */
class Solution {
    const int LOG = 18;
public:
    int sortPermutation(const vector<int>& nums) {
        if (std::is_sorted(nums.begin(), nums.end()))
            return 0;
            
        int n = nums.size();

        int ans = (1<<LOG)-1;
        for (int i = 0; i < n; i++) 
            if (nums[i] != i) 
                ans &= nums[i];

        return ans;
    }
};