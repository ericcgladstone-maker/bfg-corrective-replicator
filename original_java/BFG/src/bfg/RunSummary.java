package bfg;

import java.io.FileInputStream;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Properties;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import bfg.recorder.Recorder;
import bfg.recorder.RecorderFactory;
import bfg.recorder.SummaryRecord;

public class RunSummary {
	private static final Logger log = LoggerFactory.getLogger(RunSummary.class);

	private Properties props;

	public RunSummary(Properties props) {
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
		new RunSummary(props).run();
	}

	private void run() {
		Recorder recorder = RecorderFactory.getInstance(this.props);
		double fullFitnessValue = Double.parseDouble(this.props.getProperty("run.exit.on.fitness.value", "0.0"));
		List<SummaryRecord> summary = new ArrayList<>();
		log.info("Loading generation files");
		List<List<MutationStep>> allGenerations = recorder.loadAllGenerations();
		log.info("Loaded {} generations", allGenerations.size());
		int generation = 1;
		log.info("Creating summary records");
		for (List<MutationStep> gen : allGenerations) {
			log.debug("Generation {} size {}", generation, gen.size());
			int rank = 1;
			int genSize = gen.size();
			int numFullFitness = (int) gen.parallelStream().mapToDouble(MutationStep::getConvergingToFitness)
					.filter(d -> d >= fullFitnessValue).count();
			for (MutationStep step : gen) {
				SummaryRecord rec = new SummaryRecord();
				rec.setGeneration(generation);
				rec.setRank(rank);
				rec.setFitnessScore(step.getConvergingToFitness());
				rec.setText(step.getChildString());
				rec.setParentText(step.getParentString());
				rec.setTargetText(step.getConvergingToString());
				rec.setNumberInGeneration(genSize);
				rec.setNumberFullFitness(numFullFitness);
				rec.setFullFitnessScore(fullFitnessValue);
				summary.add(rec);
				rank++;
			}
			generation++;
		}
		log.info("Created {} summary records", summary.size());
		log.info("Writing summary file");
		recorder.write(summary);
		log.info("Done");
	}

}
