/**
 * This solution is O(n.lg(n))
 */
class Solution {
    const int LOG = 18;
public:
    int sortPermutation(vector<int>& nums) {
        if (std::is_sorted(nums.begin(), nums.end()))
            return 0;
        
        int n = nums.size();
        vector<int> pos(n);

        for (int i = 0; i < n; i++) 
            pos[nums[i]] = i;
        
        int ans = 0;
        for (int i = LOG; i >= 0; i--) {
            if (check(pos, ans^(1<<i)))
                ans ^= 1<<i;
        }

        return ans;
    }
private:
    bool check(const vector<int>& pos, int k) {
        int n = pos.size();
        for (int i = 0; i < n; i++) {
            if ((i&k) != k)
                if (pos[i] != i) 
                    return 0;
        }

        return 1;
    }
};