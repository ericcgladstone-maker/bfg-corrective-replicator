package bfg.reaper;

import java.util.List;

import bfg.MutationStep;
import bfg.RandomSelector;

public class RandomReaper implements Reaper {
	private int maxSize;

	public RandomReaper(int maxSize) {
		this.maxSize = maxSize;
	}

	@Override
	public List<MutationStep> reap(List<MutationStep> generationList) {
		List<MutationStep> survivors;
		if (generationList.size() <= maxSize) {
			survivors = generationList;
		} else {
			survivors = getRandom(maxSize, generationList);
		}
		return survivors;
	}

	private List<MutationStep> getRandom(int max, List<MutationStep> source) {
		return new RandomSelector<MutationStep>().select(max, source);
	}

	@Override
	public String description() {
		return "Random reaper keeping " + maxSize + " elements";
	}

}
