package bfg.recorder;

import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.Reader;
import java.io.Writer;
import java.lang.reflect.Type;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVPrinter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.common.io.Files;
import com.google.common.reflect.TypeToken;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import bfg.MutationStep;

public class Recorder {
	private static final Logger log = LoggerFactory.getLogger(Recorder.class);
	private static final String generationFileNamePrefix = "generation";

	private Path outPath;
	private Gson gson;

	public Recorder(Path path) {
		this.outPath = path;
		this.gson = new GsonBuilder().setPrettyPrinting().create();
	}

	public int load(List<MutationStep> generationList) {
		log.debug("Loading from {}", outPath);
		generationList.clear();
		int generation = 0;
		File outDir = this.outPath.toFile();
		if (outDir.exists()) {
			Optional<File> mostRecent = Arrays
					.stream(this.outPath.toFile().listFiles((f, n) -> n.startsWith(generationFileNamePrefix)))
					.max((f1, f2) -> Integer.compare(Integer.parseInt(Files.getFileExtension(f1.getAbsolutePath()), 10),
							Integer.parseInt(Files.getFileExtension(f2.getAbsolutePath()), 10)));
			if (mostRecent.isPresent()) {
				File mostRecentFile = mostRecent.get();
				generation = getGenerationNumFromFile(mostRecentFile);
				List<MutationStep> loadedGeneration = loadGeneration(mostRecentFile);
				generationList.addAll(loadedGeneration);
			}
		}
		if (generation == 0) {
			log.debug("No prior work found");
		} else {
			log.debug("Loaded generation {}", generation);
		}
		return generation;
	}

	private List<MutationStep> loadGeneration(File dfile) {
		@SuppressWarnings("serial")
		final Type collectionType = new TypeToken<List<MutationStep>>() {
		}.getType();
		try (Reader reader = new FileReader(dfile)) {
			List<MutationStep> loadedGeneration = this.gson.fromJson(reader, collectionType);
			return loadedGeneration;
		} catch (IOException e) {
			log.error("Error loading prior work from {}", dfile, e);
			throw new RuntimeException(e);
		}
	}

	private int getGenerationNumFromFile(File dfile) {
		return Integer.parseInt(Files.getFileExtension(dfile.getAbsolutePath()), 10);
	}

	public void write(int generation, List<MutationStep> generationList) {
		log.debug("Writing generation {} to {}", generation, outPath);
		File outDir = this.outPath.toFile();
		if (!outDir.exists()) {
			outDir.mkdir();
		}
		File genFile = new File(outDir, generationFileNamePrefix + "." + generation);
		try (Writer writer = new FileWriter(genFile)) {
			this.gson.toJson(generationList, writer);
		} catch (IOException e) {
			log.error("Error writing generation {}", generation, e);
			throw new RuntimeException(e);
		}
		log.debug("Done writing {}", genFile);
	}

	public List<List<MutationStep>> loadAllGenerations() {
		log.debug("Loading from {}", outPath);
		Map<Integer, List<MutationStep>> generationMap = new HashMap<>();
		Arrays.stream(this.outPath.toFile().listFiles((f, n) -> n.startsWith(generationFileNamePrefix)))
				.forEach(file -> generationMap.put(getGenerationNumFromFile(file), loadGeneration(file)));
		int genCount = generationMap.size();
		ArrayList<List<MutationStep>> allGenList = new ArrayList<>();
		for (int i = 1; i <= generationMap.size(); i++) {
			allGenList.add(generationMap.get(i));
		}
		log.debug("Done loading {} generations from {}", genCount, outPath);
		return allGenList;
	}

	public void write(List<SummaryRecord> summary) {
		File summaryFile = new File(outPath.toFile(), "summary.csv");
		log.debug("Writing summary file {}", summaryFile);
		try (Writer writer = new FileWriter(summaryFile);
				CSVPrinter printer = new CSVPrinter(writer, CSVFormat.EXCEL);) {
			for (SummaryRecord rec : summary) {
				printer.printRecord(rec.getGeneration(), //
						rec.getRank(), //
						rec.getFitnessScore(), //
						rec.getText(), //
						rec.getParentText(), //
						rec.getTargetText(), //
						rec.getNumberInGeneration(), //
						rec.getNumberFullFitness(), //
						rec.getFullFitnessScore() //
				);
			}
		} catch (IOException e) {
			log.error("Error writing summary", e);
			throw new RuntimeException(e);
		}
		log.debug("Done writing summary file");
	}
}
