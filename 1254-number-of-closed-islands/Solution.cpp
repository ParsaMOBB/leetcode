class Solution {
private:
    enum class Cell {
        Land,
        Water
    };

    static constexpr pair<int, int> neighbors[] = {
        {-1, 0},
        {1, 0},
        {0, -1},
        {0, 1}
    };

public:
    int closedIsland(vector<vector<int>>& grid) {
        auto cells = convertGrid(grid);
        addLandBorderMargin(cells);

        // the ring of land and every island touching the boundary
        // form one component; every other component is a closed island
        return countLandComponents(cells) - 1;
    }

private:
    vector<vector<Cell>> convertGrid(const vector<vector<int>>& grid) {
        vector<vector<Cell>> cells;
        cells.reserve(grid.size());

        for (const auto& row : grid) {
            vector<Cell> convertedRow;
            convertedRow.reserve(row.size());

            for (int cell : row) {
                convertedRow.push_back(
                    cell == 0 ? Cell::Land : Cell::Water
                );
            }

            cells.push_back(move(convertedRow));
        }

        return cells;
    }

    /**
     * Turn an NxM grid into an (N+2)x(M+2) grid
     * by adding 2 rows and 2 columns of land (L) around it
     *
     * for example :
     *                      LLLLL
     *        XXX           LXXXL
     *        XXX     -->   LXXXL
     *        XXX           LXXXL
     *        XXX           LXXXL
     *                      LLLLL
    */
    void addLandBorderMargin(vector<vector<Cell>>& grid) {
        int m = grid[0].size();

        grid.insert(
            grid.begin(),
            vector<Cell>(m, Cell::Land)
        );
        grid.push_back(vector<Cell>(m, Cell::Land));

        for (auto& row : grid) {
            row.insert(row.begin(), Cell::Land);
            row.push_back(Cell::Land);
        }
    }

    int countLandComponents(
        const vector<vector<Cell>>& grid
    ) {
        int n = grid.size();
        int m = grid[0].size();

        vector<vector<bool>> mark(n, vector<bool>(m, false));
        int cntComponents = 0;

        for (int i = 0; i < n; i++) {
            for (int j = 0; j < m; j++) {
                if (!mark[i][j] && grid[i][j] == Cell::Land) {
                    cntComponents++;
                    dfs(i, j, grid, mark);
                }
            }
        }

        return cntComponents;
    }

    void dfs(
        int i,
        int j,
        const vector<vector<Cell>>& grid,
        vector<vector<bool>>& mark
    ) {
        mark[i][j] = true;

        for (auto [di, dj] : neighbors) {
            int ni = i + di;
            int nj = j + dj;

            if (isLand(ni, nj, grid) && !mark[ni][nj]) {
                dfs(ni, nj, grid, mark);
            }
        }
    }

    bool isLand(
        int i,
        int j,
        const vector<vector<Cell>>& grid
    ) {
        int n = grid.size();
        int m = grid[0].size();

        return 0 <= i && i < n &&
               0 <= j && j < m &&
               grid[i][j] == Cell::Land;
    }
};
