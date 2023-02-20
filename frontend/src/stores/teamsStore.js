import axios from "axios";
import { defineStore } from "pinia";

export const useTeamsState = defineStore({
    id: "teams",
    state: () => ({
        filterOpen: false,
        tableExport: [],
        filterOptions: [{
            "years": [{ "start_year": "" }, { "end_year": ""}],
            "competition_categories": [{"": ""}],
            "nations": {},
        }],
        data: {
            "interval": [0, 0],
            "nation": "GER (Germany)",
            "results": 0,
            "athletes": {},
            "boat_classes": {
                'm': {
                    'junior': {
                        'single': {"JM1x": "Junior Men's Single Sculls"},
                        'double': {"JM2x": "Junior Men's Double Sculls"},
                        'quad': {"JM4x": "Junior Men's Quadruple Sculls"},
                        'pair': {"JM2-": "Junior Men's Pair"},
                        'coxed_four': {"JM4+": "Junior Men's Coxed Four"},
                        'four': {"JM4-": "Junior Men's Four"},
                        'eight': {"JM8-": "Junior Men's Eight"}
                    },
                    'u19': {},
                    'u23': {
                        'single': {"BM1x": "U23 Men's Single Sculls"},
                        'double': {"BM2x": "U23 Men's Double Sculls"},
                        'quad': {"BM4x": "U23 Men's Quadruple Sculls"},
                        'pair': {"BM2-": "U23 Men's Pair"},
                        'coxed_four': {"BM4+": "U23 Men's Coxed Four"},
                        'four': {"BM4-": "U23 Men's Four"},
                        'eight': {"BM8+": "U23 Men's Eight"},
                        'lw_single': {"BLM1x": "U23 Lightweight Men's Single Sculls"},
                        'lw_double': {"BLM2x": "U23 Lightweight Men's Double Sculls"},
                        'lw_quad': {"BLM4x": "U23 Lightweight Men's Quadruple Sculls"},
                        'lw_pair': {"BLM2-": "U23 Lightweight Men's Pair"},
                    },
                    'elite': {
                        'single': {"M1x": "Men's Single Sculls"},
                        'double': {"M2x": "Men's Double Sculls"},
                        'quad': {"M4x": "Men's Quadruple Sculls"},
                        'pair': {"M2-": "Men's Pair"},
                        'four': {"M4-": "Men's Four"},
                        'eight': {"M8+": "Men's Eight"},
                        'lw_single': {"LM1x": "Lightweight Men's Single Sculls"},
                        'lw_double': {"LM2x": "Lightweight Men's Double Sculls"},
                        'lw_quad': {"LM4x": "Lightweight Men's Quadruple Sculls"},
                        'lw_pair': {"LM2-": "Lightweight Men's Pair"},
                    },
                    'para': {
                        '1': {"PR1 M1x": "PR1 Men's Single Sculls"},
                        '2': {"PR2 M1x": "PR2 Men's Single Sculls"},
                        '3': {"PR3 M2-": "PR3 Men's Pair"}
                    }
                },
                'w': {
                    'junior': {
                        'single': {"JW1x": "Junior Women's Single Sculls"},
                        'double': {"JW2x": "Junior Women's Double Sculls"},
                        'quad': {"JW4x": "Junior Women's Quadruple Sculls"},
                        'pair': {"JW2-": "Junior Women's Pair"},
                        'coxed_four': {"JW4+": "Junior Women's Coxed Four"},
                        'four': {"JW4-": "Junior Women's Four"},
                        'eight': {"JW8-": "Junior Women's Eight"}
                    },
                    'u19': {},
                    'u23': {
                        'single': {"BW1x": "U23 Women's Single Sculls"},
                        'double': {"BW2x": "U23 Women's Double Sculls"},
                        'quad': {"BW4x": "U23 Women's Quadruple Sculls"},
                        'pair': {"BW2-": "U23 Women's Pair"},
                        'coxed_four': {"BW4+": "U23 Women's Coxed Four"},
                        'four': {"BW4-": "U23 Women's Four"},
                        'eight': {"BW8+": "U23 Women's Eight"},
                        'lw_single': {"BLW1x": "U23 Lightweight Women's Single Sculls"},
                        'lw_double': {"BLW2x": "U23 Lightweight Women's Double Sculls"},
                        'lw_quad': {"BLW4x": "U23 Lightweight Women's Quadruple Sculls"},
                        'lw_pair': {"BLW2-": "U23 Lightweight Women's Pair"},
                    },
                    'elite': {
                        'single': {"W1x": "Women's Single Sculls"},
                        'double': {"W2x": "Women's Double Sculls"},
                        'quad': {"W4x": "Women's Quadruple Sculls"},
                        'pair': {"W2-": "Women's Pair"},
                        'four': {"W4-": "Women's Four"},
                        'eight': {"W8+": "Women's Eight"},
                        'lw_single': {"LW1x": "Lightweight Women's Single Sculls"},
                        'lw_double': {"LW2x": "Lightweight Women's Double Sculls"},
                        'lw_quad': {"LW4x": "Lightweight Women's Quadruple Sculls"},
                        'lw_pair': {"LW2-": "Lightweight Women's Pair"},
                    },
                    'para': {
                        '1': {"PR1 W1x": "PR1 Women's Single Sculls"},
                        '2': {"PR2 W1x": "PR2 Women's Single Sculls"},
                        '3': {"PR3 W2-": "PR3 Women's Pair"}
                    }
                },
                'mixed': {
                    'double_2': {"PR2 Mix2x": "PR2 Mixed Double Sculls"},
                    'double_3': {"PR3 Mix2x": "PR3 Mixed Double Sculls"},
                    'four': {"PR3 Mix4+": "PR3 Mixed Coxed Four"},
                },
                'all': {
                    'all': {"Alle Bootsklassen": "Alle"}
                },
            }
        }
    }),
    getters: {
        getFilterState(state) {
            return state.filterOpen
        },
        getTeamsFilterOptions(state) {
            return state.filterOptions
        },
        getMetaData(state) {
            return state.data
        },
        getTableData(state) {
            const data = state.data.boat_classes
            const subHeaders = {
                "OPEN MEN": Object.values(data.m.elite),
                "OPEN WOMEN": Object.values(data.w.elite),
                "PARA MEN": Object.values(data.m.para),
                "PARA WOMEN": Object.values(data.w.para),
                "U23 MEN": Object.values(data.m.u23),
                "U23 WOMEN": Object.values(data.w.u23),
                "U19 MEN": Object.values(data.m.u19),
                "U19 WOMEN": Object.values(data.w.u19)
            }
            let rowValues = []
            Object.entries(subHeaders).forEach(([key, value], idx) => {
                rowValues.push(key)
                for (const item of value) {
                    if (item !== undefined && item.length > 1) {
                        const data = state.data.athletes[item[2]]
                        if (data !== undefined) {
                            rowValues.push([item[0], data.map(el => [el.name, el.id])])
                        }
                    }
                }
            })
            state.tableExport = rowValues
            return rowValues
        }
    },
    actions: {
        async fetchTeamsFilterOptions() {
            await axios.get(`${import.meta.env.VITE_BACKEND_API_BASE_URL}/get_teams_filter_options`)
                .then(response => {
                    this.filterOptions = response.data
                }).catch(error => {
                    console.error(`Request failed: ${error}`)
                })
        },
        async fetchTeams(data) {
            await axios.post(`${import.meta.env.VITE_BACKEND_API_BASE_URL}/get_teams`, {data})
                .then(response => {
                    this.data = response.data
                }).catch(error => {
                    console.error(`Request failed: ${error}`)
                })
        },
        setFilterState(filterState) {
            this.filterOpen = !filterState
        },
        exportTableData() {
             const csvContent = "data:text/csv;charset=utf-8," + this.tableExport.map(row => {
                if (Array.isArray(row)) {
                    return row.map(cell => {
                        if (typeof cell === "string") {
                            return `"${cell}"`;
                        }
                        return cell;
                    }).join(",");
                }
                return row;
            }).join("\n");
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", "teams.csv");
            document.body.appendChild(link);
            link.click();
        }
    }
})