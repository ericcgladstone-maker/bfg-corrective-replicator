package bfg.reaper;

import java.util.Properties;

import bfg.misc.Utilities;

public class ReaperFactory {
	private static final String PROP_TYPE = "reaper";

	private static final String PROP_TF_MAXELEMENTS = "reaper.topfitness.maxelements";

	private static final String PROP_RAND_MAXELEMENTS = "reaper.random.maxelements";

	private static final String PROP_DISTRIB_MAXELEMENTS = "reaper.fitnessdistribution.maxelements";

	private static final String PROP_BUCKET_TARGET_PREAMBLE = "reaper.bucketfitness.targetarraypreamble";
	private static final String PROP_BUCKET_BUCKET_CAPACITIES = "reaper.bucketfitness.capacity";
	private static final String PROP_BUCKET_TOTAL_CAPACITY = "reaper.bucketfitness.maxelements";
	private static final String PROP_BUCKET_DIVERSION_FITNESS_MINS = "reaper.bucketfitness.minfitness";

	public static Reaper getInstance(Properties props) {
		Reaper reaper;
		String reaperType = props.getProperty(PROP_TYPE);
		if ("TopFitness".equals(reaperType)) {
			reaper = new TopFitnessReaper(Integer.parseInt(props.getProperty(PROP_TF_MAXELEMENTS), 10));
		} else if ("Random".equals(reaperType)) {
			reaper = new RandomReaper(Integer.parseInt(props.getProperty(PROP_RAND_MAXELEMENTS), 10));
		} else if ("FitnessDistribution".equals(reaperType)) {
			reaper = new FitnessDistributionReaper(Integer.parseInt(props.getProperty(PROP_DISTRIB_MAXELEMENTS), 10));
		} else if ("BucketFitness".equals(reaperType)) {
			reaper = new BucketReaper(
					Utilities.getInstance().loadStringArray(props, props.getProperty(PROP_BUCKET_TARGET_PREAMBLE)),
					Utilities.getInstance().loadIntegerArray(props, PROP_BUCKET_BUCKET_CAPACITIES),
					Utilities.getInstance().loadDoubleArray(props, PROP_BUCKET_DIVERSION_FITNESS_MINS),
					Integer.parseInt(props.getProperty(PROP_BUCKET_TOTAL_CAPACITY), 10));
		} else {
			throw new RuntimeException("Unknown reaper type " + reaperType);
		}
		return reaper;
	}
}
