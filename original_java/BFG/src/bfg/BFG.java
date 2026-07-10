package bfg;

import java.io.FileInputStream;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Properties;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import bfg.corrector.Corrector;
import bfg.corrector.CorrectorFactory;
import bfg.corrector.NullCorrector;
import bfg.evaluator.Evaluator;
import bfg.evaluator.EvaluatorFactory;
import bfg.misc.StringSanitizer;
import bfg.misc.Utilities;
import bfg.mutator.Mutator;
import bfg.mutator.MutatorFactory;
import bfg.reaper.Reaper;
import bfg.reaper.ReaperFactory;
import bfg.recorder.Recorder;
import bfg.recorder.RecorderFactory;
import bfg.replicator.Replicator;
import bfg.replicator.ReplicatorFactory;

public class BFG {
	private static final Logger log = LoggerFactory.getLogger(BFG.class);

	private Properties props;

	public BFG(Properties props) {
		this.props = props;
	}

	public static void main(String[] args) {
		Properties props = new Properties();
		try (FileInputStream propFile = new FileInputStream(args[0])) {
			props.load(propFile);
		} catch (IOException ex) {
			String msg = "Could not load properties file " + args[0];
			log.error(msg, ex);
			throw new RuntimeException(msg, ex);
		}
		new BFG(props).run();
	}

	public void run() {
		// System.setProperty("java.util.concurrent.ForkJoinPool.common.parallelism","2");
		Mutator mutator = MutatorFactory.getInstance(this.props);
		Replicator replicator = ReplicatorFactory.getInstance(this.props, mutator);
		Reaper reaper = ReaperFactory.getInstance(this.props);
		Evaluator evaluator = EvaluatorFactory.getInstance(this.props);
		Corrector corrector = CorrectorFactory.getInstance(this.props);
		StatCollector stats = new StatCollector();
		Recorder recorder = RecorderFactory.getInstance(this.props);

		List<MutationStep> generationList = new ArrayList<>();
		int generation = recorder.load(generationList);
		if (generation == 0) {
			generationList.addAll(loadSeeds(this.props));
			generationList = evaluator.evaluate(generationList);
			recorder.write(generation, generationList);
			log.info("Starting from {} seeds", generationList.size());
		} else {
			log.info("Continuing from generation {}", generation);
		}
		stats.logStatistics(generationList);

		boolean preEvaluate = "true".equalsIgnoreCase(this.props.getProperty("run.evaluate.before.correction"));
		boolean nonNullCorrector = !NullCorrector.class.isInstance(corrector);
		boolean exitOnConvergence = "true".equalsIgnoreCase(this.props.getProperty("run.exit.on.convergence"));
		int minGenerations = Integer.parseInt(this.props.getProperty("run.minimum.generations.before.convergence"), 10);
		int runLength = Integer.parseInt(this.props.getProperty("run.length"));
		boolean exitOnFitness = "true".equalsIgnoreCase(this.props.getProperty("run.exit.on.fitness"));
		double exitFitnessValue = Double.parseDouble(this.props.getProperty("run.exit.on.fitness.value", "0.0"));
		int exitFitnessCount = Integer.parseInt(this.props.getProperty("run.exit.on.fitness.count", "10"));

		log.info("Configuration:");
		log.info("\tMutator: {}", mutator.description());
		log.info("\tCorrector: {}", corrector.description());
		log.info("\tEvaluator: {}", evaluator.description());
		log.info("\tReaper: {}", reaper.description());

		EvolutionProcessor processor;
		int i = 0;
		boolean earlyExit = false;
		while (i < runLength && !earlyExit) {
			i++;
			log.info("####### Processing generation {} size: {} #######", generation, generationList.size());
			processor = new EvolutionProcessor(replicator, generationList);
			log.info("Computing children");
			generationList = processor.compute();
			if (nonNullCorrector) {
				if (preEvaluate) {
					log.info("Evaluating before corrections");
					generationList = evaluator.evaluate(generationList);
					stats.logStatistics(generationList);
				}
				log.info("Correcting {} children", generationList.size());
				generationList = corrector.correct(generationList);
			}
			log.info("Evaluating children fitness");
			generationList = evaluator.evaluate(generationList);
			stats.logStatistics(generationList);
			log.info("Culling generation");
			generationList = reaper.reap(generationList);
			log.info("Statistics after reaping");
			stats.logStatistics(generationList);
			generation++;
			log.info("Recording generation {}", generation);
			recorder.write(generation, generationList);
			if (exitOnConvergence && (generation > minGenerations) && reachedConvergence(generationList)) {
				log.info("Convergence Detected");
				earlyExit = true;
			}
			if (exitOnFitness && reachedFitness(generationList, exitFitnessValue, exitFitnessCount)) {
				log.info("Target Fitness Reached");
				earlyExit = true;
			}
		}
		log.info("Done");
	}

	private Collection<MutationStep> loadSeeds(Properties props) {
		Utilities util = Utilities.getInstance();
		StringSanitizer sanitizer = StringSanitizer.getInstance();
		List<String> seedStrings = util.loadStringArray(props, "seed");
		List<MutationStep> seeds = new ArrayList<>();
		for (String seedString : seedStrings) {
			MutationStep seed = new MutationStep();
			seed.setChildString(sanitizer.sanitize(seedString));
			seeds.add(seed);
		}
		return seeds;
	}

	private boolean reachedFitness(List<MutationStep> generationList, double exitFitnessValue, int exitFitnessCount) {
		return generationList.parallelStream().mapToDouble(MutationStep::getConvergingToFitness)
				.filter(d -> d >= exitFitnessValue).count() >= exitFitnessCount;
	}

	private boolean reachedConvergence(List<MutationStep> generationList) {
		String fittestString = generationList.get(0).getChildString();
		return generationList.parallelStream().allMatch(x -> fittestString.equals(x.getChildString()));
	}

}
