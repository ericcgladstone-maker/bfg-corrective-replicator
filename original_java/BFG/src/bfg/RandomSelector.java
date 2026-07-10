package bfg;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class RandomSelector<T> {
	private static final Logger log = LoggerFactory.getLogger(RandomSelector.class);

	public List<T> select(int max, List<T> source) {
		// defensive copy in case source is immutable
		ArrayList<T> workspace = new ArrayList<>(source);
		Random rng = new Random();
		max = Math.min(max, source.size());
		log.debug("Looking for {} of {}", max, source.size());
		for (int i = 0; i < max; i++) {
			if (log.isTraceEnabled()) {
				log.trace("i={}, max={}, max-i={}", i, max, max - i);
			}
			int pick = rng.nextInt(max - i) + i;
			log.debug("Swapping {} with {}", i, pick);
			Collections.swap(workspace, i, pick);
		}
		return workspace.subList(0, max);
	}
}
