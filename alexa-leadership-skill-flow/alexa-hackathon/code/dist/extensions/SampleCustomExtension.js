"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SampleCustomExtension = void 0;
class SampleCustomExtension {
    async pickRandomDay(param) {
        let randomDayName = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        param.storyState.randomDayName = randomDayName[Math.floor(Math.random() * randomDayName.length)];
    }
}
exports.SampleCustomExtension = SampleCustomExtension;
