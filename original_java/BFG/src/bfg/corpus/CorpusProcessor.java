package bfg.corpus;

import java.io.File;
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.nio.file.FileVisitOption;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.Comparator;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CorpusProcessor {
	private static final Logger log = LoggerFactory.getLogger(CorpusProcessor.class);

	private static void deleteFileTree(Path root) throws IOException {
		if (root.toFile().exists()) {
			Files.walk(root, FileVisitOption.FOLLOW_LINKS).sorted(Comparator.reverseOrder()).map(Path::toFile)
					.peek(f -> log.debug("Deleting {}", f)).forEach(File::delete);
		}
	}

	public static void main(String[] args) throws IOException {
		Path corpusIn = Paths.get(args[0]);
		Path corpusOut = Paths.get(args[1]);
		log.info("Input direcotry: {}", corpusIn);
		log.info("Output directory: {}", corpusOut);
		log.info("Clearing output directory");
		deleteFileTree(corpusOut);
		corpusOut.toFile().mkdir();
		log.info("Processing corpus input");
		processCorpus(corpusIn, corpusOut);
		log.info("Done");
	}

	private static void processCorpus(Path in, Path out) throws IOException {
		ParagraphStringSplitter splitter = new ParagraphStringSplitter();
		HTMLTextExtractor extractor = new HTMLTextExtractor();
		Files.walkFileTree(in, new SimpleFileVisitor<Path>() {
			@Override
			public FileVisitResult preVisitDirectory(Path dir, BasicFileAttributes attrs) throws IOException {
				Path relativeSource = in.relativize(dir);
				Path relativeTarget = out.resolve(relativeSource);
				log.trace("relativeSource {} relativeTarget {}", relativeSource, relativeTarget);
				log.debug("Creating {} from {}", relativeTarget, dir);
				relativeTarget.toFile().mkdirs();
				log.info("Processing {}", dir);
				return FileVisitResult.CONTINUE;
			}

			@Override
			public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
				Path relativeSource = in.relativize(file);
				Path relativeTarget = out.resolve(relativeSource).getParent();
				String targetFileNameBase = file.getFileName().toString();
				log.debug("Writing {} to {}::{}", file, relativeTarget, targetFileNameBase);

				byte[] encoded = Files.readAllBytes(file);
				String fileText = new String(encoded, Charset.defaultCharset());
				log.trace("{} :: length {}", file, fileText.length());
				int sNum = 0;
				for (String sentence : splitter.splitParagraph(extractor.extractText(fileText))) {
					log.trace("{} : {}", ++sNum, sentence);
					Path newFile = relativeTarget.resolve(String.format("%s.%d", targetFileNameBase, sNum));
					log.debug("Writing {}", newFile);
					Files.write(newFile, sentence.trim().getBytes(StandardCharsets.UTF_8));
				}
				log.debug("{} :: sentences {}", file, sNum);

				return FileVisitResult.CONTINUE;
			}
		});
	}
}
