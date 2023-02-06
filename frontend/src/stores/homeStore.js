import axios from "axios";
import {defineStore} from "pinia";

const calenderColors = ["#26A69A", "#B3E5FC", "#00B0FF", "#0097A7", "#0017A7"]

export const useHomeStore = defineStore({
    id: "home",
    state: () => ({
        data: {
            calender_data: []
        }
    }),
    getters: {
        getCalenderData(state) {
            let calenderEntries = state.data.calender_data;
            return calenderEntries.map((entry, index) => {
                let colorIdx = null
                if (entry.customData.title.includes("World Rowing Cup")) {
                    colorIdx = 0
                } else if (entry.customData.title.includes("European") && entry.customData.title.includes("Under 19")) {
                    colorIdx = 1
                } else if (entry.customData.title.includes("European")) {
                    colorIdx = 2
                } else if (entry.customData.title.includes("Indoor")) {
                    colorIdx = 4
                } else {
                    colorIdx = 3
                }
                entry.customData["style"] = 'background-color:' + calenderColors[colorIdx];
                return entry;
            });
        }
    },
    actions: {
        async fetchCalendarData() {
            try {
                const response = await axios.get(`http://localhost:5000/calendar/`);
                this.data.calender_data = response.data;
            } catch (error) {
                console.error(error);
            }
        }
    }
});